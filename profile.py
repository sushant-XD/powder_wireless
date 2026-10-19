"""
Allocates ota-nuc1 and ota-nuc2 in the POWDER indoor over-the-air lab using
B210 USRPs. The lab has four of these (ota-nuc1 through
ota-nuc4).
The UE transmits on band n3 uplink. A gNB is assumed to already be
on the air

Instructions:
Reserve ota-nuc1, ota-nuc2, and the band n3 ranges below before
instantiating. After the nodes turn green, the startup service installs
Docker and UHD and starts the UE on ota-nuc1 and the sniffer on ota-nuc2.
Logs: ssh to the node and run `sudo docker compose logs -f controller`
in /local/rtue.

To install the software and leave it stopped, set the autostart parameter
to false and ssh to each node and run:

    sudo /local/repository/boot.sh ue
    sudo /local/repository/boot.sh sniffer
"""

import geni.portal as portal
import geni.rspec.pg as rspec

pc = portal.Context()

pc.defineParameter(
    "autostart",
    "Start the UE and sniffer when the nodes boot. "
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
    "disk_image",
    "Disk image for both NUCs.",
    portal.ParameterType.IMAGE,
    "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU24-64-STD",
)

params = pc.bindParameters()
request = pc.makeRequestRSpec()

# Band n3, 20 MHz, matching configs/srsran/ue_uhd.conf (DL ARFCN 368500,
# center 1842.5 MHz) and the uplink center in configs/sni5gect/srsgnb_band3.yaml
# (1747.5 MHz). The UE transmits on the uplink.
request.requestSpectrum(1737.5, 1757.5)
request.requestSpectrum(1832.5, 1852.5)

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

# Optional gNB on a third indoor B210. Left off because a gNB is assumed
# to already be running. Uncomment this block, reserve ota-nuc3, and the
# node will boot start-gnb.sh (srsRAN gNB, band n3, B210).
#
# gnb = request.RawPC("gnb")
# gnb.component_id = "ota-nuc3"
# gnb.component_manager_id = EMULAB
# gnb.hardware_type = "nuc8559"
# gnb.disk_image = params.disk_image
# if params.autostart:
#     gnb.addService(rspec.Execute(
#         shell="/bin/bash",
#         command="sudo /local/repository/boot.sh gnb"))
# else:
#     gnb.addService(rspec.Execute(
#         shell="/bin/bash",
#         command="sudo /local/repository/boot.sh install"))

pc.printRequestRSpec()
