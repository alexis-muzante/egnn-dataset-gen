package adhocnetwork;

import inet.node.inet.AdhocHost;
import inet.visualizer.integrated.IntegratedCanvasVisualizer;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.physicallayer.unitdisk.UnitDiskRadioMedium;

network AdhocNetwork
{
   parameters:
       @display("bgb=600,400");
   submodules:
       visualizer: IntegratedCanvasVisualizer {
           @display("p=100,100");
       }
       configurator: Ipv4NetworkConfigurator {
           @display("p=100,200");
       }
       radioMedium: UnitDiskRadioMedium {
           @display("p=100,300");
       }
       hostA: AdhocHost {
           @display("p=300,100");
       }
       hostB: AdhocHost {
           @display("p=300,300");
       }
   connections allowunconnected:
       hostA.wlan[0] <--> radioMedium.medium;
       hostB.wlan[0] <--> radioMedium.medium;
}
