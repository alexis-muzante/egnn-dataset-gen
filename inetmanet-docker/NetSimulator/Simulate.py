#!/usr/bin/env python

import os,sys
import logging
import networkx as nx
import numpy as np
import NetworkNedGenerator as nng
import multiprocessing
import traceback
import yaml
import subprocess
import math
import importlib

if (os.path.isdir("/data/ext_python")):
    sys.path.insert(0,"/data/ext_python")

min_link_bandwidth = 10000
min_buffer_size = 8000
min_queue_siz = 1



class SimWorkerException(Exception):
    """
    Exceptions generated when processing simulation file
    """
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

def prepare_results_dic(results_dic, samples_per_file, dataset_name):
    global out_path

    results_dic["ctr"] = 0
    results_dic["partial_ctr"] = 0
    results_dic["sample_per_file"] = samples_per_file
    results_dic["name"] = dataset_name
    results_dic["out_path"] = out_path
    

class Results:
    aux_dir = "/data/tmp/results"
    
    
    @classmethod
    def open_files(cls, results_dic):
        os.mkdir(cls.aux_dir)
        results_dic["t_fd"] = open(os.path.join(cls.aux_dir,"traffic.txt"),"w")
        results_dic["r_fd"] = open(os.path.join(cls.aux_dir,"simulationResults.txt"),"w")
        results_dic["fr_fd"] = open(os.path.join(cls.aux_dir,"flowSimulationResults.txt"),"w")
        results_dic["s_fd"] = open(os.path.join(cls.aux_dir,"stability.txt"),"w")
        results_dic["i_fd"] = open(os.path.join(cls.aux_dir,"input_files.txt"),"w")
        results_dic["l_fd"] = open(os.path.join(cls.aux_dir,"linkUsage.txt"),"w")
    
    @classmethod
    def close_files(cls, results_dic):
        results_dic["t_fd"].close()
        results_dic["r_fd"].close()
        results_dic["fr_fd"].close()
        results_dic["s_fd"].close()
        results_dic["i_fd"].close()
        results_dic["l_fd"].close()
    
    @classmethod
    def generate_samples_file(cls, results_dic, final = False):
        if (final):
            i0 = results_dic["ctr"] - results_dic["partial_ctr"]
        else:
            i0 = results_dic["ctr"] - results_dic["sample_per_file"]
        i1 = results_dic["ctr"] - 1
        name = "results_{}_{}_{}".format(results_dic["name"],i0,i1)
        dst_path = os.path.join(results_dic["out_path"],name)
        subprocess.call("mv {} {}".format(cls.aux_dir,dst_path), shell=True)
        tar_file = os.path.join(results_dic["out_path"],"{}.tar.gz".format(name))
        subprocess.call("tar zcf {} -C {} {}".format(tar_file,results_dic["out_path"], name), shell=True)
        subprocess.call("rm -r {}".format(dst_path), shell=True)
        
        
    
    @classmethod
    def add_sample (cls,ctr,results_dic, write_pkt_info):
        work_dir = "./data.{}".format(ctr)
        if (not os.path.isdir(cls.aux_dir)):
            os.mkdir (cls.aux_dir)


        with open(os.path.join(work_dir,"traffic.txt")) as fd, \
            open(os.path.join(cls.aux_dir,"traffic.txt"),"a") as t_fd:
            t_fd.write(fd.readline())
        with open(os.path.join(work_dir,"simulationResults.txt")) as fd, \
            open(os.path.join(cls.aux_dir,"simulationResults.txt"),"a") as r_fd:
            r_fd.write(fd.readline())
        with open(os.path.join(work_dir,"flowSimulationResults.txt")) as fd, \
            open(os.path.join(cls.aux_dir,"flowSimulationResults.txt"),"a") as fr_fd:
            fr_fd.write(fd.readline())
        with open(os.path.join(work_dir,"stability.txt")) as fd, \
            open(os.path.join(cls.aux_dir,"stability.txt"),"a") as s_fd:
            s_fd.write(fd.readline())
        with open(os.path.join(work_dir,"input_files.txt")) as fd, \
            open(os.path.join(cls.aux_dir,"input_files.txt"),"a") as i_fd:
            i_fd.write(fd.readline())
        with open(os.path.join(work_dir,"linkUsage.txt")) as fd, \
            open(os.path.join(cls.aux_dir,"linkUsage.txt"),"a") as l_fd:
            l_fd.write(fd.readline())
        
        if (write_pkt_info):
            pkt_info_src_file = os.path.join(work_dir,"pkts_info.txt") 
            pkt_info_folder = os.path.join(results_dic["out_path"],"pkts_info")
            pkt_info_dst_file = os.path.join(pkt_info_folder,"pkts_info.txt.{}".format(ctr )) 
            subprocess.call("mv {} {}".format(pkt_info_src_file,pkt_info_dst_file), shell=True)
            subprocess.call("tar zcf {}.tar.gz -C {} pkts_info.txt.{} && rm {}".format(
                pkt_info_dst_file,pkt_info_folder,ctr,pkt_info_dst_file), shell=True)


        results_dic["ctr"] += 1
        results_dic["partial_ctr"] = results_dic["ctr"] % results_dic["sample_per_file"]
        
        if (results_dic["partial_ctr"] == 0):
            cls.generate_samples_file(results_dic)
        subprocess.call("rm -r  {}".format(work_dir), shell=True)
    
    @classmethod
    def create_final_file(cls,results_dic):
        if (results_dic["partial_ctr"] != 0):
            cls.generate_samples_file(results_dic,final = True)
        subprocess.call("rm -r /data/tmp", shell=True)
        

        
#------------------------------ TOPOLOGY -------------------------------------        

levelsToS = 1 

def check_node_config(node):

    levelsQoS = 0
    if (not "schedulingPolicy" in node):
        raise SimWorkerException("Nodes should specify schedulingPolicy. It could be 'FIFO', 'SP', 'WFQ', or 'DRR'.")
    
    policy = node["schedulingPolicy"]
    if (policy != "FIFO" and policy != "SP" and policy != "WFQ" and policy != "DRR"):
        raise SimWorkerException("Node with unknown schedulingPolicy: {}. Accepted values could be 'FIFO', 'SP', 'WFQ', or 'DRR'.".format(policy))
    
    if ("tosToQoSqueue" in node):
        ToQoSqueue_str = node["tosToQoSqueue"]
        all_tos = []
        tos_qos_match = []
        queues_str = ToQoSqueue_str.split(";")
        for queue_str in queues_str:
            tos_lst = []
            for tos in queue_str.split(","):
                try:
                    tos = int(tos)
                except:
                    raise SimWorkerException("Error converting tos {} in tosToQoSqueue {}. It should be an integer.".format(tos,ToQoSqueue_str))
                if (tos in all_tos):
                    raise SimWorkerException("The ToS {} is assigned to more than one QoS queue: {}".format(tos,ToQoSqueue_str))
                if (tos < 0 or tos > levelsToS):
                    raise SimWorkerException("The used ToS for this topology should be between {} and {}: {}".format(0,levelsToS-1, ToQoSqueue_str))
                tos_lst.append(tos)
                all_tos.append(tos)
            tos_qos_match.append(tos_lst)
            levelsQoS += 1
        if (len (all_tos) != levelsToS):
            raise SimWorkerException("All ToS should be assigned to a QoS queue: Number of ToS: {}, ToS to queue assignation: {}".format(levelsToS,ToQoSqueue_str))
    else:
        ToQoSqueue_str = ""
    
    
    if (policy == "WFQ" or policy == "DRR"):
        if (not "schedulingWeights" in node):
           raise SimWorkerException("When a node is configured with 'WFQ' or 'DRR', schedulingWeights should be specified.".format(policy))
        
        weights_str = node["schedulingWeights"]
        try:
            weights_lst = list(map(float,weights_str.split(",")))
        except:
            raise SimWorkerException("Error converting the weights of the scheduling policy: {}".format(weights_str))
        
        if (levelsQoS != 0):
            if (len(weights_lst) != levelsQoS):
                raise SimWorkerException("The policy {} should define {} weights in the schedulingWeights parameter.".format(policy, levelsQoS))
        else:
            if (len(weights_lst) != levelsToS):
                raise SimWorkerException("When tosToQoSqueue is not specified, the number of weights should be one per ToS - {}-{} | levelToS: {}".format(policy,weights_str,levelsToS))
            levelsQoS = levelsToS
            ToQoSqueue_str = ";".join(list(map(str,range(levelsToS))))

        
        if (not math.isclose (np.sum(weights_lst), 100)):
            raise SimWorkerException("The sum of the weights used for the policy {} should be 100: {}".format(policy,weights_str))
    elif (policy == "FIFO"):
        levelsQoS = 1
        ToQoSqueue_str = ",".join(list(map(str,range(levelsToS))))
        node["schedulingWeights"] = "-"
    else: 
        #SP
        node["schedulingWeights"] = "-"
        if (levelsQoS == 0):
            levelsQoS = levelsToS
            ToQoSqueue_str = ";".join(list(map(str,range(levelsToS))))

    
    node["tosToQoSqueue"] = ToQoSqueue_str    
    node["levelsQoS"] = levelsQoS
            
    
    if (not "bufferSizes" in node and not "queueSizes" in node):
        raise SimWorkerException("Nodes should specify buffer size of queues")

    if ("bufferSizes" in node): 
        buffer_size = node["bufferSizes"]
    
        if (buffer_size < min_buffer_size ):
            raise SimWorkerException("Buffer size of queues should be bigger than {}: {}".format(min_buffer_size,buffer_size))
    
        buffer_str = str(buffer_size)
        for i in range(levelsQoS - 1):
            buffer_str += ",{}".format(buffer_size)
        node["bufferSizes"] = buffer_str
    else:
        queue_size = node["queueSizes"]
    
        if (queue_size < min_queue_siz ):
            raise SimWorkerException("Queue size of queues should be bigger than {}: {}".format(min_queue_siz,queue_size))
    
        queue_str = str(queue_size)
        for i in range(levelsQoS - 1):
            queue_str += ",{}".format(queue_size)
        node["queueSizes"] = queue_str

     
    
    return (True)

def check_edge_config(edge,ctr):
    if(not "bandwidth" in edge):
        raise SimWorkerException("Edges of topology file should specify bandwidth")
    try:
        bw = int(edge["bandwidth"])
    except:
        raise SimWorkerException("The bandwidth of edges should be an integer: {}".format(edge["bandwidth"]))
    if (bw % 1000 != 0):
        raise SimWorkerException("The bandwidth of edges should be multiple of 1000: {}".format(edge["bandwidth"]))
    if (bw < min_link_bandwidth):
        raise SimWorkerException("The bandwidth of edges should be bigger than {}: {}".format(min_link_bandwidth,edge["bandwidth"]))
    
    return (True)

def add_ports_to_graph(G):
    port_max_index = [0]*G.number_of_nodes()
    for node in G:
        for adj in G[node]:
            if (adj < node):
                continue
            G[node][adj]['port'] = port_max_index[node]
            G[adj][node]['port'] = port_max_index[adj]
            port_max_index[node] += 1
            port_max_index[adj] += 1

def process_graph_file(graph_file,ctr):
    global out_graphs_dir
    global levelsToS
    work_dir = "./data.{}".format(ctr)
    
    if (not graph_file.startswith("/data/")):
        graph_file = os.path.join("/data",graph_file)
    
    if(not os.path.isfile(graph_file)):
        raise SimWorkerException("{}: Topology file not found: {}".format(ctr,graph_file))
    try:
        G = nx.read_gml(graph_file,destringizer=int)
    except:
        raise SimWorkerException("{}: Error in the topology file {}. It should use GML format".format(ctr,graph_file))
    
    if (G.is_directed() == True):
        raise SimWorkerException("{}: Error in the topology file {}. Topology should be undirected.".format(ctr, graph_file))
    
    if (G.is_multigraph() == True):
        raise SimWorkerException("{}: Error in the topology file {}. Topology should not be multigraph.".format(ctr, graph_file))
    
    if (not nx.is_connected(G)):
        raise SimWorkerException("{}: Error in the topology file {}. Topology has isolated nodes.".format(ctr, graph_file))
    
    if (not "levelsToS" in G.graph):
        G.graph["levelsToS"] = 1
    levelsToS = G.graph["levelsToS"]
    
    for i in range(len(G)):
        try:
            check_node_config(G.nodes[i])
        except SimWorkerException as e:
            raise SimWorkerException("{}: Error in the topology file {}. {}".format(ctr, graph_file, e))
    
    for e in G.edges():
        try:
            check_edge_config(G[e[0]][e[1]],ctr)
        except SimWorkerException as e:
            raise SimWorkerException("{}: Error in the topology file {}. {}".format(ctr, graph_file, e))
    
    
    G = G.to_directed()
    add_ports_to_graph(G)
    
    grph_file_name = os.path.join(out_graphs_dir,os.path.basename(graph_file))
    nx.write_gml(G, grph_file_name)
    
    out_ned_file = os.path.join(work_dir,"Network_topology.ned")
    nng.create_ned_file(G,"topology", out_ned_file)
    return (G)
    
#------------------------------ ROUTING-------------------------------------

def saveRouting(G,routing_matrix,output_dir="srcRouting"):
        os.mkdir(output_dir)
        netSize = len(G)
        for src in range(netSize):
            R = np.zeros((netSize, netSize)) - 1
            for dst in range(netSize):
                if (src == dst):
                    R[src,dst] = -1
                    continue
                path = routing_matrix[src,dst]
                s0 = path[0]
                for s1 in path[1:]:
                    R[s0][dst] = G[s0][s1]['port']
                    s0 = s1
            
            routing_file = "Routing_src_"+str(src)+".txt"
            
            newFile = os.path.join(output_dir,routing_file)
            np.savetxt(newFile, R, fmt='%1i', delimiter=',', newline=',\n')

def process_routing_file(G,routing_file,ctr):
    global out_routings_dir
    work_dir = "./data.{}".format(ctr)
    if (not routing_file.startswith("/data")):
        routing_file = os.path.join("/data",routing_file)
    
    if(not os.path.isfile(routing_file)):
        raise SimWorkerException("{}:Routing file not found: {}".format(ctr,routing_file))
    
    net_size = len (G)
    path_matrix = np.zeros((net_size,net_size),dtype=object)
    with open(routing_file) as fd:
        for line in fd:
            nodes_str = line.split(",")
            try:
                path = list(map(int,nodes_str))
            except:
                raise SimWorkerException("{}: Error in the routing file {}. Paths of routing file must be described " \
                             "as a sequence of nodes ids separated by commas.".format(ctr,routing_file))
                 
            if (len(path)==1):
                continue
            
            if (len(set(path)) != len(path)):
                raise SimWorkerException("{}: Error in the routing file {}. Paths of routing file should not have loops: ".format(ctr,routing_file,line))
            
            for n in path:
                if (n >= net_size):
                    raise SimWorkerException("{}: Error in the routing file {}. Node included in the path not belongs to the graph".format(ctr,routing_file,line))
            
            path_matrix[path[0],path[-1]]=path
            
    routing_path = os.path.join(work_dir,"srcRouting")
    saveRouting(G,path_matrix,routing_path)
            
    routing_name = os.path.splitext(os.path.basename(routing_file))[0]
    output_routing = os.path.join(out_routings_dir,routing_name)
    if (not os.path.isdir(output_routing)):
        subprocess.call("cp -r {} {}".format(routing_path,output_routing), shell=True)
       

            
        
#--------------------------------- TRAFFIC MATRIX ----------------------------------

    
def process_traffic_file(G,tm_file,ctr):
    min_avg_bw = 10
    min_pkt_size = 50
    max_pkt_size = 72000
    
    exponential = 0
    cbr = 1
    onoff = 2
    td_py_def = 3
    general = 0
    sd_py_def = 1
    
    work_dir = "./data.{}".format(ctr)
    if (not tm_file.startswith("/data")):
        tm_file = os.path.join("/data",tm_file)
    
    if(not os.path.isfile(tm_file)):
        raise SimWorkerException("{}:Traffic matrix file not found: {}".format(ctr,tm_file))
    
    net_size = len(G)
    
    with open(tm_file) as fd:
        line_ctr = 0
        flows_lst = []
        tm_matrix = np.zeros((net_size,net_size),dtype=object)
        for i in range(net_size):
            for j in range(net_size):
                tm_matrix[i,j] = []
        
        avg_bw_lst = []
        for line in fd:
            line = line.strip()
            line_ctr += 1
            fields = line.split(",")
            if (len(fields) < 7):
                raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. Check valid format in documentation".format(ctr,tm_file,line_ctr))

            try:
                src = int(fields[0])
            except:
                raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. Src node should be an integer".format(ctr,tm_file,line_ctr))
            try:
                dst = int(fields[1])
            except:
                raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. Dst node should be an integer".format(ctr,tm_file,line_ctr))
            
            flow_id = len(tm_matrix[src,dst])
            try:
                avg_bw = round(float(fields[2]),6)
                avg_bw_lst.append(avg_bw)
            except:
                raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. Avg bandwidth node should be an integer or float".format(ctr,tm_file,line_ctr))
                
            
            
            if (src < 0 or dst < 0 or src >= net_size or dst >= net_size):
                raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. Src node and dst node should belong to the graph".format(ctr,tm_file,line_ctr))
            
            
            if (avg_bw < min_avg_bw):
               raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. Average bandwidth of the path should be bigger than {}: {} ".format(ctr,tm_file,line_ctr,min_avg_bw,avg_bw))
            
            
            try:
                time_dist_type = int(fields[3])
            except:
                raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. Time distribution field should be an integer ({})".format(ctr,tm_file,line_ctr,fields[3]))
            

            # Find ptr to size distributio parameters
            sd_idx = 0
            if (time_dist_type == td_py_def):
                ext_time_dis_name  = fields[4]
                try:
                    td_module = importlib.import_module(ext_time_dis_name)
                    ext_time_dis_class = getattr(td_module, ext_time_dis_name)
                except:
                    raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. The module {} is not found in /data/ext_python.".format(ctr,tm_file,line_ctr,ext_time_dis_name))
                try:
                    td_num_parameters = ext_time_dis_class.num_stream_parameters()
                except:
                    raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. The module {} don't have the method num_stream_parameters".format(ctr,tm_file,line_ctr,ext_time_dis_name))
                sd_idx = 5 + td_num_parameters
            elif (time_dist_type == onoff):
                sd_idx = 6
            else:
                sd_idx = 4

            #======================  Process size distribution =========================
            try:
                size_dist_type = int(fields[sd_idx])
            except:
                raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. Size distribution field should be an integer ({})".format(ctr,tm_file,line_ctr,fields[sd_idx]))

            
            avg_pkt_size = 0
            if (size_dist_type == general):
                try:
                    size_dist_params = list(map(float,fields[sd_idx+1:-1]))
                except:
                    raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. Size distribution fields should be integer or float {}".format(ctr,tm_file,line_ctr,fields[ds_idx+1:]))
                
                if (len(size_dist_params) % 2 != 0):
                    raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. Size distribution parameters are couples of packet size and probability".format(ctr,tm_file,line_ctr))
                cdf_prob = 0
                aux_txt = ""
                general_dist_params = list(zip(*(iter(size_dist_params),) * 2))
                if (len(general_dist_params)>8):
                    raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. A maximum of 8 packet size can be defined in a packet size distribution.".format(ctr,tm_file,line_ctr))
                    
                
                for (pkt_size,prob) in general_dist_params:
                    if (pkt_size < min_pkt_size or pkt_size > max_pkt_size):
                        raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. Packet Size should be between {} and {}".format(ctr,tm_file,line_ctr,min_pkt_size,max_pkt_size))
                    if (prob < 0 or prob > 1):
                        raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. Probability expressed as so much per one".format(ctr,tm_file,line_ctr))
                    cdf_prob += prob
                    avg_pkt_size += pkt_size*prob
                    aux_txt += "{},{},".format(pkt_size,prob)
                if (not math.isclose(cdf_prob,1)):
                    raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. The sum of probabilities of all packets sizes should be one".format(ctr,tm_file,line_ctr))
                avg_pkt_size = round(avg_pkt_size,3)
                size_dist_txt = "3,{},{},{}".format(avg_pkt_size,len(general_dist_params),aux_txt[:-1])
            elif(size_dist_type == sd_py_def):
                ext_size_dis_name  = fields[sd_idx+1]
                try:
                    sd_module = importlib.import_module(ext_size_dis_name)
                    ext_size_dis_class = getattr(sd_module, ext_size_dis_name)
                except:
                    raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. The module {} is not found in /data/ext_python.".format(ctr,tm_file,line_ctr,ext_size_dis_name))
                try:
                    num_parameters = ext_size_dis_class.num_stream_parameters()
                except:
                    raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. The module {} don't have the method num_stream_parameters".format(ctr,tm_file,line_ctr,ext_size_dis_name))
                if (num_parameters != len(fields[sd_idx+2:-1])):
                    raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. The module {} uses " \
                                             "{} parameters and {} where provided".format(ctr,tm_file,line_ctr,ext_size_dis_name, \
                                            num_parameters, len(fields[sd_idx+2:-1])))    
                # Generate an instance of SizeDistribution to get the avg_pkt_size
                try:
                    params = list(map(float,fields[sd_idx+2:-1]))
                except:
                    raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. The parameters provided to the module {}" \
                                             " should be integers or floats: {}".format(ctr,tm_file,line_ctr,ext_size_dis_name,fields[sd_idx+2:-1]))
                ext_size_dis_instance = ext_size_dis_class(src,dst,flow_id,*params)
                try:
                    avg_pkt_size = ext_size_dis_instance.get_average()
                except:
                    raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. The module {} don't have the method get_average".format(ctr,tm_file,line_ctr,ext_size_dis_name))
                
                try:
                    sd_num_parameters = ext_size_dis_class.num_stream_parameters()
                except:
                    raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. The module {} don't have the method num_stream_parameters".format(ctr,tm_file,line_ctr,ext_time_dis_name))

                if (sd_num_parameters > 0):
                    size_dist_txt = "5,{},{},{}".format(avg_pkt_size,ext_size_dis_name,",".join(fields[sd_idx+2:-1]))
                else:
                    size_dist_txt = "5,{},{}".format(avg_pkt_size,ext_size_dis_name)
                  
            else:
                raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. Unknown traffic size distribution: {}".format(ctr,tm_file,line_ctr, size_dist_type))
               

            #======================  Process time distribution =========================
            
            if (time_dist_type == exponential):
                time_dist_txt ="0,{},{},10".format(avg_bw,round(avg_bw/avg_pkt_size,6))
            elif(time_dist_type == cbr):
                time_dist_txt = "1,{},{}".format(avg_bw,round(avg_bw/avg_pkt_size,6))
            elif(time_dist_type == onoff):
                try:
                    on_time = float(fields[4])
                except:
                    raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. On time of ON-OFF distribution should be an integer or float".format(ctr,tm_file,line_ctr))
                try:
                    off_time = float(fields[5])
                except:
                    raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. Off time of ON-OFF distribution should be an integer or float".format(ctr,tm_file,line_ctr))
                time_dist_txt = "4,{},{},{},{},10".format(avg_bw,round(avg_bw/avg_pkt_size,6),on_time,off_time)
            elif(time_dist_type == td_py_def):
                # Check if all parameters are doubles
                try:
                    params = list(map(float,fields[5:5+td_num_parameters]))
                except:
                    raise SimWorkerException("{}: Error using traffic matrix file {} at line {}. The parameters provided to the module {}" \
                                             " should be integers or floats: {}".format(ctr,tm_file,line_ctr,ext_time_dis_name,fields[5:5+td_num_parameters]))
                if (td_num_parameters > 0):
                    time_dist_txt = "7,{},{},{}".format(avg_bw,ext_time_dis_name,",".join(fields[5:5+td_num_parameters]))
                else:
                    time_dist_txt = "7,{},{}".format(avg_bw,ext_time_dis_name)
            
            # Final line
            ToS = int(fields[-1])
            tm_matrix[src,dst].append("{},{},{}".format(time_dist_txt,size_dist_txt,ToS))

            
    tm_line = str(round(np.max(avg_bw_lst),6))+"|"
    for src in range(net_size):
        for dst in range (net_size):
            if (len(tm_matrix[src,dst]) == 0):
                tm_line += "-1,0,-1,0,0;"
            else:
                for flow in tm_matrix[src,dst]:
                    tm_line += flow+":"
                tm_line = tm_line[:-1]+";"
    
    tm_new_file = os.path.join(work_dir,"traffic.txt.all")
    with open(tm_new_file,"w") as fd:
        fd.write(tm_line)
            
#------------------------------------------------------------------------

def prepare_simulation(line,ctr):
    work_dir = "./data.{}".format(ctr)
    os.mkdir(work_dir)
    
    camps = line.split(",")
    graph_file = camps[0]
    routing_file = camps[1]
    tm_file = camps[2]
    
    try:
        G = process_graph_file(graph_file,ctr)
        process_routing_file(G,routing_file,ctr)
        process_traffic_file(G,tm_file,ctr)
        with open(os.path.join(work_dir,"input_files.txt"),"w") as fd:
            routing_name = os.path.splitext(os.path.basename(routing_file))[0]
            graph_name = os.path.basename(graph_file)
            fd.write("{};{};{}\n".format(ctr,graph_name,routing_name))
    except SimWorkerException as e:
        logger.error(e)
        subprocess.call("rm -r {}".format(work_dir), shell=True)
        return(1)

    subprocess.call("cp /usr/src/NetSimulator/simulator/bin/* {}".format(work_dir), shell=True)

    return(0)

def prepare_output_dir(name = None, rm_prev_results = False, write_pkt_info = False):
    root_path = "/data/results"
    aux_dir = "/data/tmp"
    if (os.path.isdir(aux_dir)):
        logger.error("No more than one image can be running using the same mount point." \
                     " If it is not your case, remove tmp folder of the mount point before" \
                     " starting the container.")
        exit(1)
    
    
    if (name):
        root_path = os.path.join(root_path,name)
    
    if (os.path.isdir(root_path)):
        if (rm_prev_results):
            subprocess.call("rm -r {}".format(root_path), shell=True)
        else:
            logger.error("The folder {} already exits. Remove it before starting container".format(root_path))
            exit(1)
            
    os.mkdir (aux_dir)
    
    
    graphs_path = os.path.join(root_path,"graphs")
    routing_path = os.path.join(root_path,"routings")
    
    os.makedirs(graphs_path)
    os.mkdir(routing_path)
    if (write_pkt_info):
        pkts_info_path = os.path.join(root_path,"pkts_info")
        os.mkdir(pkts_info_path)

    subprocess.call("cp /usr/src/NetSimulator/datanetAPI.py {}".format(root_path), shell=True)
    
    return((root_path,graphs_path,routing_path))
    

def run_simulation(ctr,write_pkt_info,lock,results_state_dict):
    work_dir = "./data.{}".format(ctr)
    with open(os.path.join(work_dir,"omnetpp.ini"),"a") as fd:
        use_pkt_info = "true" if write_pkt_info else "false"
        fd.write("**.writePktInfo = {} ".format(use_pkt_info))
    cmd = "cd {} && ./NetSimulator omnetpp.ini -u Cmdenv".format(work_dir)
    
    subprocess.call(cmd, shell=True,stdout=subprocess.DEVNULL)
    results_file = os.path.join(work_dir,"simulationResults.txt")
    if (not os.path.isfile(results_file)):
        logger.error("{}: KO: Simulation doesn't finish properly".format(ctr))
        subprocess.call("rm -r {}".format(work_dir), shell=True)
        return
    with open(os.path.join(work_dir,"stability.txt")) as fd:
        line = fd.readline()
        if (not "OK" in line):
            camps = line.split(";")
            if (camps[2] == "UNSTABLE"):
                logger.error("{}: KO: Simulation is not stable".format(ctr))
            else:
                logger.error("{}: KO: Simulation doesn't finish properly -> {}".format(ctr,camps[2]))

            subprocess.call("rm -r {}".format(work_dir), shell=True)
            return
    
    with lock:
        try:
            Results.add_sample(ctr,results_state_dict,write_pkt_info)
            logger.info("{}: OK".format(ctr))
        except:
            traceback.print_exc()
    


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
file_hundler = logging.FileHandler("/data/out.log",mode='w')
logger.addHandler(file_hundler)                

# Read configuration file
if (os.path.isfile("/data/conf.yml")):
    with open ("/data/conf.yml","r") as fd:
        cfg = yaml.safe_load(fd)
    
    if ("threads" in cfg):
        num_threads = int(cfg["threads"])
    else:
        num_threads = 1
    if ("samples_per_file" in cfg):
        samples_per_file = int(cfg["samples_per_file"])
    else:
        samples_per_file = 25
    if ("dataset_name" in cfg):
        dataset_name = cfg["dataset_name"]
    else:
        dataset_name = "dataset"
    if ("rm_prev_results" in cfg):
        rm_prev_str = cfg["rm_prev_results"].lower()
        if (rm_prev_str == "y" or 
            rm_prev_str == "yes" or 
            rm_prev_str == "true"):
            rm_prev_results = True
        elif (rm_prev_str == "n" or 
            rm_prev_str == "no" or 
            rm_prev_str == "false"):
            rm_prev_results = False
        else:
            logger.eror("Configuration file: rm_prev_results should be 'y' or 'n'")
            exit(1)
    else:
        rm_prev_results = False

    if ("write_pkt_info" in cfg):
        w_pinfo_str = cfg["write_pkt_info"].lower()
        if (w_pinfo_str == "y" or 
            w_pinfo_str == "yes" or 
            w_pinfo_str == "true"):
            write_pkt_info = True
        elif (w_pinfo_str == "n" or 
            w_pinfo_str == "no" or 
            w_pinfo_str == "false"):
            write_pkt_info = False
        else:
            logger.eror("Configuration file: write_pkt_info should be 'y' or 'n'")
            exit(1)
    else:
        write_pkt_info = False
    
    
else:
    logger.warning("No configuration file found (/data/conf.yml). Using default values")
    num_threads = 1
    samples_per_file = 25
    dataset_name = "dataset"
    rm_prev_results = False
    write_pkt_info = False
    
    




(out_path,out_graphs_dir,out_routings_dir) = prepare_output_dir(dataset_name, rm_prev_results, write_pkt_info)


pool = multiprocessing.Pool(num_threads)
m = multiprocessing.Manager()
lock = m.Lock()
results_state_dict = m.dict()
prepare_results_dic(results_state_dict, samples_per_file, dataset_name)
if (not os.path.isfile("/data/simulation.txt")):
    logger.error("No simulation file found (/data/simulation.txt). Simulation cancelled. ")
    exit(1)

with open ("/data/simulation.txt") as fd:
    ctr = -1
    for line in fd:
        ctr += 1
        if (prepare_simulation(line.strip(),ctr)!=0):
            continue
        #run_simulation(ctr,write_pkt_info,lock,results_state_dict)
        pool.apply_async(run_simulation,args=(ctr,write_pkt_info,lock,results_state_dict))
    pool.close()
    pool.join()
    Results.create_final_file(results_state_dict)
        
 

