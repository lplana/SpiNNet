Basic SpiNNaker network testbed
===============================


Development Platform
--------------------

This software is based on the SpiNNaker Graph-Front-End (GFE) platform.
The GFE must be installed to use this software. For further information
about the GFE see:

[GFE introduction](http://spinnakermanchester.github.io/graph_front_end/5.0.0/index.html)

[GFE github repository](https://github.com/SpiNNakerManchester/SpiNNakerGraphFrontEnd)

As with most SpiNNaker software, this repository contains C code --that
runs on SpiNNaker-- which implements the actual neural network, and python
code --that runs on the host machine-- which manages the distribution of
tasks across SpiNNaker cores and sets up the communications network
to support inter-core communication. This code is also responsible for
the downloading of data to SpiNNaker and the collection of results.

Acknowledgments
---------------

Ongoing development of the SpiNNaker Project has been supported by
the EU ICT Flagship Human Brain Project under Grants FP7-604102, H2020-720270,
H2020-785907 and H2020-945539.
LA Plana is supported by the RAIN Hub, which is
funded by the Industrial Strategy Challenge Fund, part of the government’s
modern Industrial Strategy. The fund is delivered by UK Research and
Innovation and managed by EPSRC under grant EP/R026084/1.

We gratefully acknowledge these institutions for their support.
