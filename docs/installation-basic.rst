=============================
emodpy-typhoid installation
=============================

Follow the steps below to install emodpy-typhoid.

    .. note::

        Currently, an IDM VPN connection is required to run the example.

#.  Open a command prompt and create a virtual environment in any directory you choose. The
    command below names the environment "v-emodpy-typhoid", but you may use any desired name::

        python -m venv v-emodpy-typhoid

#.  Activate the virtual environment:

    * For Windows, enter the following::

        v-emodpy-typhoid\Scripts\activate

    * For Linux, enter the following::

        source v-emodpy-typhoid/bin/activate

#.  Install emodpy-typhoid packages::

        pip install emodpy_typhoid

    If you are on Linux, also run::

        pip install keyrings.alt

#.  Open a command prompt and clone the emodpy-typhoid GitHub repository to a local directory using the following command::

        git clone https://github.com/InstituteforDiseaseModeling/emodpy-typhoid.git

#.  Verify installation by running the included Python example, ``example.py``, located in /examples/start_here::

        python example.py

    Upon completion you can view the results in |COMPS_s|.

#.  When you are finished, deactivate the virtual environment by entering the following at a command prompt::

        deactivate
