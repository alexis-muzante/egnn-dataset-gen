//
// DigitalTwinNetwork.ned
// Red para generar el dataset para el gemelo digital de una red WiFi adhoc con BATMAN

package inet.examples.manetrouting.digitaltwin;

import inet.common.scenario.ScenarioManager;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.node.inet.AdhocHost;
import inet.physicallayer.wireless.ieee80211.packetlevel.Ieee80211ScalarRadioMedium;

network DigitalTwinNetwork
{
    parameters:
        int numHosts = default(5);
        @display("bgb=800,800");
    submodules:
        radioMedium: Ieee80211ScalarRadioMedium {
            parameters:
                @display("p=100,200;is=s");
        }
        configurator: Ipv4NetworkConfigurator {
            parameters:
                config = xml("<config><interface hosts='*' address='192.168.x.x' netmask='255.255.255.0'/></config>");
                @display("p=100,100;is=s");
        }
        scenarioManager: ScenarioManager {
            parameters:
                @display("p=50,50;is=s");
        }
        host[numHosts]: AdhocHost {
            parameters:
                @display("i=device/laptop;r=,,#707070");
                mobility.typename = "StationaryMobility";
                // Se añade un módulo de logging personalizado para registrar datos de posición,
                // potencia de transmisión y estado de transmisión (one-hot)
                logger.typename = "HostLogger";
        }
    connections allowunconnected:
}
