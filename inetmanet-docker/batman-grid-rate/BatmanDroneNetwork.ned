//
// This program is property of its copyright holder. All rights reserved.
//

package inet.examples.manetrouting.batmandronenetwork;


import inet.environment.common.PhysicalEnvironment;


import inet.common.scenario.ScenarioManager;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.networklayer.ipv4.RoutingTableRecorder;
import inet.node.inet.AdhocHost;
import inet.physicallayer.wireless.ieee80211.packetlevel.Ieee80211ScalarRadioMedium;




//
// TODO
//
network BatmanDroneNetwork
{
    parameters:
        int numRXHosts;
        int numTXHosts;
        int numRXTXHosts;
        int numRelays;
        @display("bgb=1250,1250");
    submodules:
        physicalEnvironment: PhysicalEnvironment {
            parameters:
                @display("p=131.53847,86.15385");
        }
        radioMedium: Ieee80211ScalarRadioMedium {
            parameters:
                @display("p=130.76924,168.46155");
        }
        configurator: Ipv4NetworkConfigurator {
            parameters:
                config = xml("<config><interface hosts='*' address='145.236.x.x' netmask='255.255.0.0'/></config>");
                @display("p=100,100;is=s");
        }
        routingTableRecorder: RoutingTableRecorder {
            parameters:
                @display("p=100,300;is=s");
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

