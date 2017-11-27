#!/bin/env  python
# This is the pair-end pipeline for tgirt sequencing
# Mapping with hisat + bowtie local
# and extract tRNA reads for reassigning counts


from __future__ import division, print_function
import time
import glob
import argparse
import sys
from tgirt_map.mapping_tools import sample_object

def getopt():
    parser = argparse.ArgumentParser(description='Pipeline for mapping and counting for TGIRT-seq paired end data')
    parser.add_argument('-1', '--fastq1', 
              help = 'pairedEnd fastq file (read1)', required=True)
    parser.add_argument('-2', '--fastq2', 
              help = 'pairedEnd fastq file (read2). Optional: only needed for paired-end', default=None)
    parser.add_argument('-o','--outdir', 
              help = 'result directory that all resulting/intermediate files will be stored\n' + \
                                         'will create 1. $resultpath/trimmed\n' + \
                                         '            2. $resultpath/hisat\n'  + \
                                         '            3. $resultpath/bowtie2\n' + \
                                         '            4. $resultpath/mergeBam (all useful result files)\n',
                        required=True)
    parser.add_argument('-x', '--hisat_index', 
              help = 'hisat2 index', required=True)
    parser.add_argument('-y', '--bowtie2_index', 
              help = 'bowtie2 index', required=True)
    parser.add_argument('-b','--bedpath', 
              help = 'bed folder for gene counting', required=True)
    parser.add_argument('-s','--splicesite', 
              help = 'splice site file generated by hisat', required=True)
    parser.add_argument('-t','--tRNAindex' , 
              help = 'bowtie2 index for tRNA, for better tRNA counting', required=True)
    parser.add_argument('-r','--rRNAindex' , 
              help = 'bowtie2 index for rRNA, for better rRNA counting', required=True)
    parser.add_argument('-e','--rRNA_tRNA_index' , 
              help = 'bowtie2 index for rRNA and tRNA combined', required=True)
    parser.add_argument('-p', '--threads', default=1, type=int, 
              help = 'number of cores to be used for the pipeline (default:1)')
    parser.add_argument('--TTN', action='store_true',  
              help = 'used TTN primer')
    parser.add_argument('--umi', default=0, type=int,
              help = "Number of UMI bases from 5' of R1 (default = 0)")
    parser.add_argument('--count_all', action='store_true',
              help = "Ignore UMI for counting, only evaluated with --umi option")
    parser.add_argument('--dry', action='store_true', help = "Dry run")
    parser.add_argument('--skip_trim', action='store_true',  
              help = 'DEBUG: skip trimming')
    parser.add_argument('--skip_premap', action='store_true',  
              help = 'DEBUG: skip premapping tRNA and rRNA')
    parser.add_argument('--skip_hisat', action='store_true',  
              help = 'DEBUG: skip hisat')
    parser.add_argument('--skip_bowtie', action='store_true',  
              help = 'DEBUG: skip bowtie')
    parser.add_argument('--skip_post_process_bam', action='store_true',  
              help = 'DEBUG: skip combining BAM, multimap reassignment and BED file conversion')
    parser.add_argument('--skip_remap', action='store_true',  
              help = 'DEBUG: skip tRNA/rRNA remapping')
    parser.add_argument('--skip_count', action='store_true',  
              help = 'DEBUG: skip counting')
    args = parser.parse_args()
    return args


def main():
    programname = sys.argv[0]
    start = time.time()

    args = getopt()
    process_sample = sample_object(args)
    process_sample.make_result_dir()

    if not args.skip_trim:
        process_sample.trimming()

    if not args.skip_premap:
        process_sample.premap_tRNA_rRNA()

    if not args.skip_hisat:
        process_sample.hisat_map()

    if not args.skip_bowtie:
        process_sample.bowtie_map()

    if not args.skip_post_process_bam:
        process_sample.combined_aligned()

        if args.umi > 0 and not args.count_all:
            process_sample.dedup_bam()

        process_sample.combined_filter()
        process_sample.make_alignment_bed()

    if not args.skip_remap:
        process_sample.generate_tRNA_remap()

    if not args.skip_count:
        process_sample.generate_tRNA_count()
        process_sample.generate_rRNA_count()
        process_sample.generate_all_count()

    end = time.time()
    usedTime = end - start
    print('Finished: %s in %.3f hr ' %(process_sample.samplename ,usedTime/3600), file=sys.stderr)
    return 0

if __name__ == '__main__':
    main()
