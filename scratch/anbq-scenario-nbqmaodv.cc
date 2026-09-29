/*
 * [A-NBQ] imported from nbqmaodv-fanet@5725ea6 scratch/fanet-scenario-nbqmaodv.cc; only file names changed (fanet- -> anbq-).
 * anbq-scenario-nbqmaodv.cc -- FANET scenario for the nbqmaodv routing module.
 * STEP11: the scenario body lives in anbq-core.h; this file only selects the routing helper.
 */
#include "ns3/nbqmaodv-module.h"

#include "anbq-core.h"

static std::unique_ptr<Ipv4RoutingHelper>
MakeRouting(const std::string& proto, const AttrList& attrs)
{
    if (proto == "NBQ-MAODV")
        return Make<NbqmaodvHelper>(attrs);
    NS_FATAL_ERROR("Unknown protocol: " << proto);
    return nullptr;
}

int
main(int argc, char* argv[])
{
    return FanetMain(argc, argv, "NBQ-MAODV", &MakeRouting);
}
