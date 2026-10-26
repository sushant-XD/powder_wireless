"""
Three indoor OTA NUCs with USB B210s (defaults: ota-nuc1 UE, ota-nuc2
sni5gect sniffer, ota-nuc3 srsRAN gNB + Open5GS). There is no experiment
LAN; the radios talk over the air on band n3 (20 MHz FDD). Reserve the
three NUCs and the n3 ranges below before instantiating.

Instructions:
Reserve ota-nuc1, ota-nuc2, ota-nuc3, and n3 spectrum 1737.5-1757.5 MHz
and 1832.5-1852.5 MHz before instantiating. The experiment page can show
Ready while startup scripts are still running. Wait until List View
Startup is Finished on all three nodes. ota-nuc3 docker-builds Open5GS
on the first boot and takes longer than the others.

Logs (after Finished):

    # ue or sniffer node
    cd /local/rtue && sudo docker compose logs -f controller

    # gnb node
    sudo docker logs -f open5gs_5gc
    sudo docker logs -f srsran_gnb

To install only and start later, set autostart false, then ssh to each
node and run the matching role:

    # on ue
    sudo /local/repository/boot.sh ue
    # on sniffer
    sudo /local/repository/boot.sh sniffer
    # on gnb
    sudo /local/repository/boot.sh gnb
"""

import geni.portal as portal
import geni.rspec.pg as rspec
import geni.rspec.emulab.spectrum as spectrum

pc = portal.Context()

pc.defineParameter(
    "autostart",
    "Start the UE, sniffer, and gNB+Open5GS when the nodes boot. "
    "Set false to install Docker and UHD only; start later with boot.sh.",
    portal.ParameterType.BOOLEAN,
    True,
)
pc.defineParameter(
    "ue_node",
    "Indoor OTA NUC for the software UE (B210 is USB-attached).",
    portal.ParameterType.STRING,
    "ota-nuc1",
)
pc.defineParameter(
    "sniffer_node",
    "Indoor OTA NUC for the sni5gect sniffer.",
    portal.ParameterType.STRING,
    "ota-nuc2",
)
pc.defineParameter(
    "gnb_node",
    "Indoor OTA NUC for the srsRAN gNB and Open5GS (B210 is USB-attached).",
    portal.ParameterType.STRING,
    "ota-nuc3",
)
pc.defineParameter(
    "disk_image",
    "Disk image for the NUCs.",
    portal.ParameterType.IMAGE,
    "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU24-64-STD",
)

params = pc.bindParameters()
request = pc.makeRequestRSpec()

# Band n3, 20 MHz, matching configs/srsran/ue_uhd.conf (DL ARFCN 368500,
# center 1842.5 MHz) and the uplink center in configs/sni5gect/srsgnb_band3.yaml
# (1747.5 MHz). The UE transmits on the uplink.
request.requestSpectrum(1737.5, 1757.5, 0)
request.requestSpectrum(1832.5, 1852.5, 0)

EMULAB = "urn:publicid:IDN+emulab.net+authority+cm"


def add_b210_nuc(client_id, component_id, role):
    node = request.RawPC(client_id)
    node.component_id = component_id
    node.component_manager_id = EMULAB
    node.hardware_type = "nuc8559"
    node.disk_image = params.disk_image
    # autostart true: boot.sh <role> installs and starts the controller.
    # autostart false: boot.sh install only
    if params.autostart:
        command = "sudo /local/repository/boot.sh %s" % role
    else:
        command = "sudo /local/repository/boot.sh install"
    node.addService(rspec.Execute(shell="/bin/bash", command=command))
    return node


add_b210_nuc("ue", params.ue_node, "ue")
add_b210_nuc("sniffer", params.sniffer_node, "sniffer")
add_b210_nuc("gnb", params.gnb_node, "gnb")

pc.printRequestRSpec()
