//
// This program is property of its copyright holder. All rights reserved.
//

package inet.examples.manetrouting.testnetwork;

import inet.common.scenario.ScenarioManager;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.networklayer.ipv4.RoutingTableRecorder;
import inet.node.inet.AdhocHost;
import inet.physicallayer.wireless.ieee80211.packetlevel.Ieee80211ScalarRadioMedium;
import inet.visualizer.canvas.integrated.IntegratedCanvasVisualizer;

//
// TODO
//
network TestNetwork
{
    parameters:
        int numRXHosts;
        int numTXHosts;
        int numRXTXHosts;
        int numRelays;
        @display("bgb=650,650");
    submodules:
        visualizer: IntegratedCanvasVisualizer {
            @display("p=50,100");
        }
        radioMedium: Ieee80211ScalarRadioMedium {
            parameters:
                @display("p=50,200;is=s");
        }
        configurator: Ipv4NetworkConfigurator {
            parameters:
                config = xml("<config><interface hosts='*' address='145.236.x.x' netmask='255.255.0.0'/></config>");
                @display("p=50,300;is=s");
        }
        routingTableRecorder: RoutingTableRecorder {
            parameters:
                @display("p=50,400;is=s");
        }
        relay[numRelays]: AdhocHost {
            parameters:
                @display("i=device/pocketpc_s;r=,,#707070");

        }
        rxhost[numRXHosts]: AdhocHost {
            parameters:
                @display("i=device/pocketpc_s;r=,,#707070");

        }
        txhost[numTXHosts]: AdhocHost {
            parameters:
                @display("i=device/pocketpc_s;r=,,#707070");

        }
        rxtxhost[numRXTXHosts]: AdhocHost {
            parameters:
                @display("i=device/pocketpc_s;r=,,#707070");

        }
    connections allowunconnected:
}

