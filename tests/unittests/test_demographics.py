import os
import unittest

import numpy
import pandas as pd


import emodpy_typhoid.demographics.TyphoidDemographics as TyphoidDemographics


class DemographicTest(unittest.TestCase):
    def setUp(self) -> None:
        print(f"\n{self._testMethodName} started...")
        current_dir = os.path.dirname(os.path.realpath(__file__))
        self.out_folder = os.path.join( current_dir, 'demo_output' )

    def test_basic_node_default(self):
        demog = TyphoidDemographics.fromBasicNode()
        self.assertEqual(demog.nodes[0].birth_rate, None)
        self.assertEqual(demog.nodes[0].lat, 0)
        self.assertEqual(demog.nodes[0].lon, 0)
        self.assertEqual(demog.nodes[0].id, 1)
        self.assertEqual(demog.nodes[0].default_population, 1000)
        self.assertEqual(demog.nodes[0].pop, 1e6)

    def test_basic_node(self):
        lat = 1
        lon = 2
        pop = 1000
        name = "demo"
        forced_id = 2
        demog = TyphoidDemographics.fromBasicNode(lat=lat, lon=lon, pop=pop, name=name, forced_id=forced_id)
        self.assertEqual(demog.nodes[0].birth_rate, None)
        self.assertEqual(demog.nodes[0].lat, lat)
        self.assertEqual(demog.nodes[0].lon, lon)
        self.assertEqual(demog.nodes[0].id, forced_id)
        self.assertEqual(demog.nodes[0].default_population, 1000)
        self.assertEqual(demog.nodes[0].pop, 1000)
        self.assertEqual(demog.nodes[0].node_attributes.latitude, lat)
        self.assertEqual(demog.nodes[0].node_attributes.longitude, lon)
        self.assertEqual(demog.nodes[0].node_attributes.initial_population, pop)
        self.assertEqual(demog.nodes[0].node_attributes.name, name)

    def test_from_template_node_default(self):
        demog = TyphoidDemographics.fromBasicNode()
        self.assertEqual(demog.nodes[0].birth_rate, None)
        self.assertEqual(demog.nodes[0].lat, 0)
        self.assertEqual(demog.nodes[0].lon, 0)
        self.assertEqual(demog.nodes[0].id, 1)
        self.assertEqual(demog.nodes[0].default_population, 1000)
        self.assertEqual(demog.nodes[0].pop, 1e6)

    def test_from_template_node(self):
        lat = 1
        lon = 2
        pop = 1000
        name = "demo"
        forced_id = 2
        demog = TyphoidDemographics.from_template_node(lat=lat, lon=lon, pop=pop, name=name, forced_id=forced_id)
        self.assertEqual(demog.nodes[0].birth_rate, None)
        self.assertEqual(demog.nodes[0].lat, lat)
        self.assertEqual(demog.nodes[0].lon, lon)
        self.assertEqual(demog.nodes[0].id, forced_id)
        self.assertEqual(demog.nodes[0].default_population, 1000)
        self.assertEqual(demog.nodes[0].pop, 1000)
        self.assertEqual(demog.nodes[0].node_attributes.latitude, lat)
        self.assertEqual(demog.nodes[0].node_attributes.longitude, lon)
        self.assertEqual(demog.nodes[0].node_attributes.initial_population, pop)
        self.assertEqual(demog.nodes[0].node_attributes.name, name)

    def test_from_params(self):
        numpy.random.seed(0)  # to get same random number for calculating population
        totpop = 1e5
        num_nodes = 250
        frac_rural = 0.1
        implicit_config_fns = []
        demog = TyphoidDemographics.from_params(tot_pop=totpop, num_nodes=num_nodes, frac_rural=frac_rural)
        self.assertEqual(demog.idref, "from_params")
        self.assertEqual(len(demog.node_ids), num_nodes)
        sum_pop = 0
        for node in demog.nodes:
            sum_pop += node.pop
        self.assertAlmostEqual(sum_pop, totpop, delta=5)

    def test_from_params_from_nodes(self):
        numpy.random.seed(0)  # to get same random number for calculating population
        totpop = 1e5
        lat_grid = 3
        lon_grid = 2
        num_nodes = [lat_grid, lon_grid]
        frac_rural = 0.1
        demog = TyphoidDemographics.from_params(tot_pop=totpop, num_nodes=num_nodes, frac_rural=frac_rural).to_dict()
        self.assertEqual(len(demog['Nodes']), lat_grid*lon_grid)
        sum_pop = 0
        for node in demog['Nodes']:
            sum_pop += node['NodeAttributes']['InitialPopulation']
        self.assertAlmostEqual(sum_pop, totpop, delta=5)

    def test_from_csv(self):
        input_file = os.path.join("data", "demographics", "nodes.csv")
        demog = TyphoidDemographics.from_csv(input_file)
        self.assertEqual(demog.idref, "No_Site")
        with open(input_file, 'r') as demog_file:
            demog_df = pd.read_csv(demog_file)

        self.assertListEqual(demog_df['lat'].values.tolist(), [int(node.lat) for node in demog.nodes])
        self.assertListEqual(demog_df['lon'].values.tolist(), [int(node.lon) for node in demog.nodes])
        self.assertListEqual(demog_df['pop'].values.tolist(), [int(node.pop) for node in demog.nodes])
        self.assertListEqual(demog_df['node_id'].values.tolist(), [int(node.id) for node in demog.nodes])


