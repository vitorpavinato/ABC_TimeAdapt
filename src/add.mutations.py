#!/usr/bin/python3.6

import allel
import msprime
import numpy as np
import pyslim
import scipy.stats as st
import pandas as pd


def main():
    # get
    sample_id, coverage, is_ancient, is_modern, is_dr, total_ancient, sample_size, t0 = read_sample_info()

    ttratio = 2.0/1.0
    sim_i = 1
    batch_id = 1
    project = "test"
    N = 200
    mu = 1.25e-08
    seed = 123456789
    na = 11
    ts = (0,  22,  46,  71,  78,  85, 119, 146, 208, 290, 305, 384)
    ss = (4,  1,  1,  2,  2,  1,  1,  1,  1,  1,  1,  1)
    sequencing_error = 0.005

    np.random.seed(seed)

    # add demography here
    demogr_event = [msprime.PopulationParametersChange(time=1000, initial_size=300, population_id=0)]

    # read tree, recapitate & add mutations
    treesq = pyslim.load("results/" + project + "/" + str(batch_id) + "/slim" + str(sim_i) + ".tree")
    # tree = treesq.first()
    # print(tree.draw(format="unicode"))

    # simplify tree sequence keeping nodes for the sampled individuals and their roots
    sample_individuals = np.random.choice(treesq.individuals_alive_at(ts[0]), ss[0], replace=False)
    for x in range(1, na + 1):
        sample_individuals = np.concatenate([sample_individuals, treesq.individuals_alive_at(ts[x])])
    keep_nodes = []
    for samp_i in sample_individuals:
        keep_nodes.extend(treesq.individual(samp_i).nodes)
    treesq = treesq.simplify(keep_nodes, keep_input_roots = True)
    #sample_individuals = chr_arm_treesq.individuals_alive_at(ts[0])
    #for x in range(1, na + 1):
    #    sample_individuals = np.concatenate([sample_individuals, chr_arm_treesq.individuals_alive_at(ts[x])])

    # read genome intervals (e.g. chromosome arms start and end)
    # and recombination rates from file
    start_chr_arm, end_chr_arm, rec_rate_chr_arm = read_genome_intervals()
    num_of_genome_intervals = len(start_chr_arm)

    # loop over genome intervals: recapitate, mutate, calculate sumstats
    for gi in range(0, num_of_genome_intervals):
        genome_interval = np.array([[start_chr_arm[gi], end_chr_arm[gi]]])
        gi_treesq = treesq.keep_intervals(genome_interval, simplify=False)
        gi_treesq = gi_treesq.ltrim()
        gi_treesq = pyslim.SlimTreeSequence(gi_treesq.rtrim())
        gi_treesq = gi_treesq.recapitate(recombination_rate=rec_rate_chr_arm[0],
                                         Ne=N,
                                         demographic_events=demogr_event,
                                         model="dtwf")
        gi_treesq = pyslim.SlimTreeSequence(msprime.mutate(gi_treesq, rate=mu))

        geno_data = empty_genotype_array(n_loci=gi_treesq.num_mutations,
                                         n_samples=sample_size,
                                         ploidy=2)
        positions = []
        locus = 0
        for variant in gi_treesq.variants():
            positions.append(round(variant.position))
            #print(positions)
            var_genotypes = variant.genotypes
            #print("--------------------------------")
            #print(var_genotypes)
            num_reads = st.poisson.rvs(mu=coverage, size=sample_size)
            transversion_SNP = True
            if st.uniform.rvs() < ttratio / (ttratio + 1):
                transversion_SNP = False
            # print(num_reads)
            for i in range(0, 2 * sample_size, 2):
                geno_data[locus, int(i / 2)] = snp_calling(true_genotype=var_genotypes[i:(i + 2)],
                                                           f_num_reads=num_reads[int(i / 2)],
                                                           transversion=transversion_SNP)
            locus = locus + 1



        ac = geno_data.count_alleles()
        pi = allel.mean_pairwise_difference(ac)
        n_obs, minmax, mean, var, skew, kurt = st.describe(pi)
        print("Mean pw diff= " + str(mean) + " for genome interval " + str(gi))



    #ac = geno_data.count_alleles()
    #pi = allel.sequence_diversity(positions, ac, start=1, stop=1000000)
    #print(pi)
    
    #pi_w, windows, n_bases, counts = allel.windowed_diversity(positions, ac, size=100000, start=1, stop=1000000)
    #n_obs, minmax, mean, var, skew, kurt = st.describe(pi_w)
    #print(n_obs)
    #print(minmax)
    #print(mean)
    #print(var)
    #print(skew)
    #print(kurt)


def read_sample_info(sample_info_file="data/SampleInfoTest.csv"):
    '''
    Read csv file with information on sample. Format of the file:
    --------------------------------------------------------------------------
    sampleID,           age14C,  age14Cerror,  year,  coverage,  damageRepair
    B_Ju_hoan_North-4,  NA,      NA,           2010,  40.57,     TRUE
    S_Ju_hoan_North-1,  NA,      NA,           2010,  46.49,     TRUE
    BallitoBayA,        1980,    20,           NA,    12.94,     FALSE
    BallitoBayB,        2110,    30,           NA,    1.25,      TRUE
    --------------------------------------------------------------------------

    :param sample_info_file: path of file
    :return:
    '''
    info = pd.read_csv(sample_info_file, skipinitialspace=True)
    sample_id = info.sampleID
    # age14C = info.age14C
    # age14Cerror = info.age14Cerror
    # ageBCAD = info.year
    coverage = info.coverage
    is_ancient = np.isnan(info.year)
    is_modern = np.isnan(info.age14C)
    is_dr = info.damageRepair
    total_ancient = sum(is_ancient)
    sample_size = len(info)
    t0 = max(info.year)
    return sample_id, coverage, is_ancient, is_modern, is_dr, total_ancient, sample_size, t0

info_file = open("data/SampleInfoTest.txt", "r")
for line in info_file:
    line.split()


def read_recombination_map(recombination_map_file="data/recombination_map_msprime.txt"):
    '''
    Read file with positions for start and end of chromosomes and
    recombination rates for each chromosome. Format:
    -------------------------------------
    0 1.14856e-08
    249218992 0.5
    249218993 1.10543e-08
    492309989 0.5
    492309990 1.12796e-08
    690184517 0.5
    -------------------------------------

    :param recombination_map_file:
    :return:
    '''
    file_recomb_map = open(recombination_map_file, "r")
    positions = []
    rates = []
    for line in file_recomb_map:
        p, r = line.split()
        positions.append(int(p))
        rates.append(float(r))
    return positions, rates


def read_genome_intervals(genome_intervals_file="data/genome_intervals.txt"):
    '''
    read file with information on the starting position and end position of
    each chromosome arm (centromeres removed)

    :param genome_intervals_file:
    :return:
    '''
    file_genome_intervals = open(genome_intervals_file, "r")
    start = []
    end = []
    rates = []
    for line in file_genome_intervals:
        v1, v2, v3 = line.split()
        start.append(int(v1))
        end.append(int(v2))
        rates.append(float(v3))
    return start, end, rates


def snp_calling(true_genotype, f_num_reads, error_rate=0.005, reads_th=1, score_th=10,
                ratio_th=3, dr=True, transversion=True):
    '''
    snp_calling function takes perfect simulated data from one locus of one diploid individual and
    adds missing data and error according to the number of reads of the site, error rate of the
    sequencing technology and, for ancient DNA not sequenced from damage repair (dr) libraries,
    creates missing data for transition SNPs (since they cannot be distinguished from aDNA damage)

    :param true_genotype:
    :param f_num_reads:
    :param error_rate:
    :param reads_th:
    :param score_th:
    :param ratio_th:
    :param dr:
    :param transversion:
    :return:
    '''
    if dr is False and transversion is False:
        genotype_call = [-1, -1]
    elif f_num_reads >= reads_th:
        derived_count = sum(true_genotype)
        p_derived = derived_count / 2. * (1 - error_rate) + (1 - derived_count / 2.) * error_rate
        derived_reads = st.binom.rvs(f_num_reads, p_derived)
        ancestral_reads = f_num_reads - derived_reads
        if f_num_reads >= score_th:
            if derived_reads == 0:
                genotype_call = [0, 0]
            elif ancestral_reads == 0:
                genotype_call = [1, 1]
            else:
                ratio_of_scores = derived_reads / ancestral_reads
                if (ratio_of_scores >= 1 / ratio_th) & (ratio_of_scores <= ratio_th):
                    genotype_call = [0, 1]
                elif derived_reads > ancestral_reads:
                    genotype_call = [1, 1]
                else:
                    genotype_call = [0, 0]
        else:
            random_allele = st.binom.rvs(1, derived_reads / f_num_reads)
            genotype_call = np.full(2, random_allele)
    else:
        genotype_call = [-1, -1]
    return genotype_call


def empty_genotype_array(n_loci,n_samples,ploidy = 2):
    '''
    Creates a genotype array with all values as missing (-1) for a given number
    of samples, loci and ploidy

    :return: empty_ga
    '''
    empty_ga = allel.GenotypeArray(np.full((n_loci, n_samples, ploidy), -1), dtype='i1')
    return empty_ga


###########################
if __name__ == "__main__":
    main()


