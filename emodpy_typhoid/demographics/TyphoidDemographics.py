from emod_api.demographics.Demographics import Demographics, Node
import emod_api.demographics.Demographics as Demog

class TyphoidDemographics(Demographics):
    """
        This class is derived from emod_api.demographics' Demographics class so that we can set 
        certain defaults for Typhoid in construction. As we add other disease types, the 
        generalizations and speicfics will become clearer.
    """
    def __init__(self, nodes, idref="Gridded world grump2.5arcmin", base_file=None):
        super().__init__( nodes, idref, base_file )
        # The following is for back-compat with older versions of the model which looked for these keys unconditionally.
        self.raw["Defaults"]["IndividualAttributes"]["PrevalenceDistributionFlag"] = 0
        self.raw["Defaults"]["IndividualAttributes"]["PrevalenceDistribution1"] = 0
        self.raw["Defaults"]["IndividualAttributes"]["PrevalenceDistribution2"] = 0
        #super().SetDefaultProperties()

def fromBasicNode(lat=0, lon=0, pop=1e6, name=1, forced_id=1):
    """
        This function creates a single-node TyphoidDemographics instance from the params you give it. 

        Args:
            lat: latitude (not really used)
            lon: longitude (not really used)
            pop: population. Defaults to 1 million.
            name: node name (not really used)
            forced_id: node id (not really used)

        Returns:
            GENERIC_SIM demographics instance which can be customized and/or written to file.
    """
    new_nodes = [ Node(lat=lat, lon=lon, pop=pop, name=name, forced_id=forced_id) ]
    return TyphoidDemographics(nodes=new_nodes)

def from_template_node(lat=0, lon=0, pop=1e6, name=1, forced_id=1 ):
    """
        Create a single-node TyphoidDemographics instance from the params you give it. 

        Args:
            lat: latitude (not really used)
            lon: longitude (not really used)
            pop: population. Defaults to 1 million.
            name: node name (not really used)
            forced_id: node id (not really used)

        Returns:
            GENERIC_SIM demographics instance which can be customized and/or written to file.
    """
    new_nodes = [ Node(lat=lat, lon=lon, pop=pop, name=name, forced_id=forced_id) ]
    return TyphoidDemographics(nodes=new_nodes)

def from_params(tot_pop=1e6, num_nodes=100, frac_rural=0.3, id_ref="from_params" ):
    """
    Create a multi-node :py:class:`~emodpy_typhoid.demographics.typhoidDemographics`
    instance as a synthetic population based on a few parameters.

    Args:
        tot_pop: The total human population in the node.
        num_nodes: The number of nodes to create.
        frac_rural: The fraction of the population that is rural.
        id_ref: Method describing how the latitude and longitude values are created
            for each of the nodes in a simulation. "Gridded world" values use a grid 
            overlaid across the globe at some arcsec resolution. You may also generate 
            the grid using another tool or coordinate system.

    Returns:
        A :py:class:`~emodpy_typhoid.demographics.typhoid` instance.
    """
    typhoid_demog = Demog.from_params(tot_pop, num_nodes, frac_rural, id_ref )
    nodes = typhoid_demog.nodes
    return TyphoidDemographics(nodes=nodes, idref=id_ref )

def from_csv( pop_filename_in, site="No_Site", min_node_pop = 0 ):
    """
    Create a multi-node :py:class:`~emodpy_typhoid.demographics.TyphoidDemographics`
    instance from a CSV file describing a population.

    Args:
        pop_filename_in: The path to the demographics file to ingest.
        pop_filename_out: The path to the file to output.
        site: A string to identify the country, village, or trial site.

    Returns:
        A :py:class:`~emodpy_malaria.demographics.MalariaDemographics` instance.
    """
    typhoid_demog = Demog.from_csv( pop_filename_in )
    nodes = []
    for node in typhoid_demog.nodes:
        if node.pop >= min_node_pop:
            nodes.append( node )
        else:
            print( f"Purged node {node.id} coz not enough people ({node.pop} < {min_node_pop})." )

    return TyphoidDemographics(nodes=nodes, idref=site)
