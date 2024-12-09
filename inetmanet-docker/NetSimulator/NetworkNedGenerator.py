#!/usr/bin/python3

import argparse
import networkx as nx
import sys
import os


def nodeText (node, levelsQoS, queue_sizes, bufferSizes, ports, policy, policyWeights,tosToQoSqueue):
    return ("        node%d: Server {\n" \
            "            id = %d;\n" \
            "            numNodes = numNodes;\n" \
            "            **.levelsQoS = %d;\n"
            "            **.queueSizes = \"%s\";\n" \
            "            **.bufferSizes = \"%s\";\n" \
            "            **.schedulingPolicy = \"%s\";\n" \
            "            **.schedulingWeights = \"%s\";\n" \
            "            **.tosToQoSqueue = \"%s\";\n"\
            "            gates:\n" \
            "                port[%d];\n" \
            "        }\n" % (node, node, levelsQoS, queue_sizes, bufferSizes, policy, policyWeights,tosToQoSqueue,ports))

def channelText(bw):
    return ("        channel Channel%s extends ned.DatarateChannel\n" \
            "        {\n" \
            "            datarate = %s;\n" \
            "        }\n" % (bw,bw))
    
    
    return ()    
  
def connctionText (srcNode,srcPort,dstNode,dstPort,bandwidth1,bandwidth2,delay1,delay2):
    line =""
    if (bandwidth1 == bandwidth2 and delay1 == delay2):
        line = "      node%d.port[%d] <--> Channel%s {delay = %s;} <--> node%d.port[%d];\n" \
            % (srcNode, srcPort, bandwidth1, delay1, dstNode, dstPort)
    else:
        line = "      node%d.port[%d] --> Channel%s {delay = %s;} --> node%d.port[%d];\n" \
            % (srcNode, srcPort, bandwidth1, delay1, dstNode, dstPort)
        line = line + "      node%d.port[%d] <-- Channel%s {delay = %s;} <-- node%d.port[%d];\n" \
            % (srcNode, srcPort, bandwidth2, delay2, dstNode, dstPort)
    return (line)
  
def controllerCoonectionText (node):
    return ("      tController.out[%d] --> " \
            "{ @display(\"ls=grey,1,d\"); } --> " \
            "node%d.tControl;\n" % (node,node))

def getQueueSize (node):
    res = "-"
    if ("queueSize" in node):
        res = str(node["queueSize"])
    if ("queueSizes" in node):
        res = str(node["queueSizes"])
    
    return (res)

def getBufferSize (node):
    res = "-"
    if ("bufferSizes" in node):
        res = str(node["bufferSizes"])
    
    return (res)

def create_ned_file(G,topology_name, out_ned_file):
    num_nodes = len (G.nodes)
    
    nodesStr = ""
    connctionsStr = ""
    channelsStr = ""
    tControllerConStr = ""
    
    bw_list = []
    
#     edges = list(G.edges)
#     edge = edges[0]
    
    links_added = []
    for node in G:
        for adj in G[node]:
            if (adj,node) in links_added:
                continue
            links_added.append((node,adj))
            srcPort = G[node][adj]['port']
            dstPort = G[adj][node]['port']
            bw1 = str(int(int(G[node][adj]['bandwidth'])/1000))+"kbps"
            bw2 = str(int(int(G[adj][node]['bandwidth'])/1000))+"kbps"
            
            if (not bw1 in bw_list):
                bw_list.append(bw1)
            if (not bw2 in bw_list):
                bw_list.append(bw2)
            
            delay1 = "0ms"
            delay2 = "0ms"
            if ("delay" in G[node][adj]):
                delay1 = str(int(float(G[node][adj]['delay'])*1000))+"ms"
            if ("delay" in G[adj][node]):
                delay2 = str(int(float(G[adj][node]['delay'])*1000))+"ms"
            connctionsStr += connctionText(node,srcPort,adj,dstPort,bw1,bw2,delay1,delay2)
    
    for node in G:
        max_port = len(G[node].keys()) #Number of adjacencies
        levelsQoS = 1 if not "levelsQoS" in G.nodes[node] else  G.nodes[node]["levelsQoS"]
        policy = "FIFO" if not "schedulingPolicy" in G.nodes[node] else  G.nodes[node]["schedulingPolicy"]
        queueSizes = getQueueSize(G.nodes[node])
        bufferSizes = getBufferSize(G.nodes[node])
        if (queueSizes == "-" and bufferSizes == "-"):
            bufferSizes = ("32000"*levelsQoS)
            bufferSizes = bufferSizes[:-1]
        policyWeights = "-" if not "schedulingWeights" in G.nodes[node] else  G.nodes[node]["schedulingWeights"]
        tosToQoSqueue = "-" if not "tosToQoSqueue" in G.nodes[node] else  G.nodes[node]["tosToQoSqueue"]
        nodesStr += nodeText (node,levelsQoS,queueSizes,bufferSizes,max_port,policy, policyWeights, tosToQoSqueue)
        tControllerConStr += controllerCoonectionText(node)
    
    for bw in bw_list:
        channelsStr += channelText(bw)
    
    if (not "levelsToS" in G.graph):
        levelsToS = 1
    else:
        levelsToS = G.graph["levelsToS"]
    
    fd = open(out_ned_file,"w")
    
    
    text =  "package netsimulator;\n" \
            "network  Network_"+topology_name+"\n" \
            "{\n" \
            "    parameters:\n" \
            "        int numNodes = "+str(num_nodes)+";\n" \
            "        int levelsToS = "+str(levelsToS)+";\n" \
            "    types:\n"+ channelsStr+ \
            "    submodules:\n" \
            "        statistic: Statistic {\n" \
            "            numNodes = numNodes; \n" \
            "        } \n" 
    text += nodesStr
    text += "        tController: NetTrafficController {\n" \
            "            numNodes = numNodes; \n" \
            "            levelsToS = levelsToS; \n" \
            "            gates:\n" \
            "                out[numNodes];\n" \
            "         }\n\n"
            
    text += "    connections:\n\n"+connctionsStr+"\n\n"
    text += "      statistic.out --> { @display(\"ls=grey,1,d\"); } --> tController.in;\n"
    text += tControllerConStr
    text += "}"
             
    fd.write(text)
    fd.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", help="Name of the topology", required=True)
    parser.add_argument("-o", help="Directory where files are saved. By default ./simulator/params/<topology name>")
    parser.add_argument("-g", help="GML File to process", required=True)
    args = parser.parse_args()
    
    graph_file = args.g
    topology_name = args.n
    ned_file_name = "Network_"+topology_name+".ned"
    if (args.o):
        out_path = args.o
    else:
        out_path = "./simulator/params/"+topology_name
    out_ned_file = out_path+"/"+ned_file_name
    
    if (not os.path.isfile(graph_file)):
        print ("Graph file doesn't exist: "+args.g)
        exit()
    G = nx.nx.read_gml(args.g, destringizer=int)
    
    create_ned_file(G,topology_name, out_ned_file)

if __name__ == "__main__":
    main()
