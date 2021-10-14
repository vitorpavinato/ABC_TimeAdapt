#    TimeAdapt: joint inference of demography and selection
#    Copyright (C) 2021  Miguel de Navascués, Uppsala universitet, INRAE
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
import timeadapt
import tempfile # for creating temporal files on testing
import allel
import pytest

_, temp_config_file_1 = tempfile.mkstemp()
with open(temp_config_file_1, 'w') as f:
  f.write("[Settings]\n")
  f.write("verbose = 0\n")
  f.write("project = test\n")
  f.write("batch = 1\n")
  f.write("sample_file = data/sample.txt\n")
  f.write("genome_file = data/genome.txt\n")

_, temp_config_file_2 = tempfile.mkstemp()
with open(temp_config_file_2, 'w') as f:
  f.write("[Settings]\n")
  f.write("verbose = 1.2\n")
  f.write("project = test\n")
  f.write("batch = 1\n")
  f.write("sample_file = data/sample.txt\n")
  f.write("genome_file = data/genome.txt\n")

_, temp_sim_file_1 = tempfile.mkstemp()
with open(temp_sim_file_1, 'w') as f:
  f.write("[Simulation]\n")
  f.write("sim=1\n")
  f.write("[Sample]\n")
  f.write("ss=4 1 1 1 1 1 1 1 1 1 1 1 1 1\n")
  f.write("chrono_order=0 1 2 3 10 9 4 8 6 5 7 12 13 16 11 15 14\n")
  f.write("[Demography]\n")
  f.write("N=11 85 200 200 200 37 10 30 71\n")
  f.write("[Genome]\n")
  f.write("mu=8.6106e-08\n")
  f.write("ttratio=2\n")
  f.write("seq_error=0.005\n")
  f.write("[Seeds]\n")
  f.write("seed_coal=106\n")
  f.write("seed_mut=408\n")
  
result_config_1_sim_1 = {"project":"test", "batch":"1", "sim":"1",
                         "verbose":0,
                         "genome_file":"data/genome.txt", "sample_file":"data/sample.txt",
                         "ss":[4,1,1,1,1,1,1,1,1,1,1,1,1,1],
                         "chrono_order":[0,1,2,3,10,9,4,8,6,5,7,12,13,16,11,15,14],
                         "N":[11,85,200,200,200,37,10,30,71],
                         "mu":8.6106e-08,
                         "ttratio":2, "seq_error":0.005,
                         "seed_coal":106, "seed_mut":408}

result_config_2_sim_1 = {"project":"test", "batch":"1", "sim":"1",
                         "verbose":1,
                         "genome_file":"data/genome.txt", "sample_file":"data/sample.txt",
                         "ss":[4,1,1,1,1,1,1,1,1,1,1,1,1,1],
                         "chrono_order":[0,1,2,3,10,9,4,8,6,5,7,12,13,16,11,15,14],
                         "N":[11,85,200,200,200,37,10,30,71],
                         "mu":8.6106e-08,
                         "ttratio":2, "seq_error":0.005,
                         "seed_coal":106, "seed_mut":408}

test_input_files = [pytest.param(temp_config_file_1, temp_sim_file_1, result_config_1_sim_1, id="1_1"),
                    pytest.param(temp_config_file_2, temp_sim_file_1, result_config_2_sim_1, id="2_1")]

@pytest.mark.parametrize("temp_config_file,temp_sim_file,expected_result", test_input_files)
def test_get_options(temp_config_file,temp_sim_file,expected_result):
  project, batch, sim, genome_file, sample_file, verbose, ss, chrono_order, N, mu, ttratio, seq_error, seed_coal, seed_mut = \
           timeadapt.get_options(proj_options_file = temp_config_file, sim_options_file = temp_sim_file)
  assert type(project) is str
  assert project == expected_result["project"]
  assert type(batch) is str
  assert batch == expected_result["batch"]
  assert type(sim) is str
  assert sim == expected_result["sim"]
  assert type(verbose) is int
  assert verbose ==  expected_result["verbose"]
  assert type(genome_file) is str
  assert genome_file == expected_result["genome_file"]
  assert type(sample_file) is str
  assert sample_file == expected_result["sample_file"]
  assert type(ss) is list
  for i in ss:
    assert type(i) is int
  assert ss == expected_result["ss"]
  assert type(chrono_order) is list
  for i in chrono_order:
    assert type(i) is int
  assert chrono_order == expected_result["chrono_order"]
  assert type(N) is list
  for i in N:
    assert type(i) is int
  assert N == expected_result["N"]
  assert type(mu) is float
  assert mu == pytest.approx(expected_result["mu"])
  assert type(seed_coal) is int
  assert seed_coal == expected_result["seed_coal"]
  assert type(seed_mut) is int
  assert seed_mut == expected_result["seed_mut"]