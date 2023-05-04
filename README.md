# NDN Name-Based Access Control on FABRIC

Named Data Networking (NDN) is a project with intent on changing how the current IP architecture looks and works. The current IP architecture is in need of redesign as it was built with a vision to work as a communication network, but the Internet has grown to be more of a distribution network. With this new proposed architecture, questions have arisen as to how security and trust will be implemented. We are using the FABRIC testbed to implement the NDN architecture, as well as to implement and integrate Name-Based Access Control (NAC). In future work, we additionally seek to implement the NDN Project’s trust schema specification for automated data and interest packet signing and authentication.

This project is based on work completed by Ashwin Nair, Jason Womack, Toby Sinkinson, and Yingqiang Yuan. Their work implements the NDN-DPDK Project on the FABRIC Testbed. Their original work may be viewed [here](https://github.com/initialguess/fabric-ndn)

## Usage

To use this notebook on FABRIC:

* clone the repository: git clone https://github.com/agaouett/fabric_nac
* navigate to the repo directory: cd fabric-nac
* make the notebooks: make notebooks
* open the fabric-nac notebook, follow the steps to conifgure your environment, the proceed with the project
* *fabric-nac.ipynb* contains all of the necessary steps to demonstrate the prototype NAC implementation.

## References

[NDN-DPDK GitHub](https://github.com/usnistgov/ndn-dpdk)

[DPDK GitHub](https://github.com/DPDK/dpdk)

[NVIDIA MLX OFED](https://docs.nvidia.com/networking/display/MLNXOFEDv531001/Downloading+Mellanox+OFED)

[FABRIC NDN Project](https://github.com/initialguess/fabric-ndn)

