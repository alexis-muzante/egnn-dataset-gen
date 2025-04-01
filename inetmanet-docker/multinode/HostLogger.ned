package inet.examples.manetrouting.digitaltwin;

simple HostLogger
{
    parameters:
        double logInterval @unit(s) = default(1s);
    gates:
        input in;
}