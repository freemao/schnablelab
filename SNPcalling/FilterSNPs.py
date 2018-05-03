# -*- coding: UTF-8 -*-

"""
Filter SNPs using bcftools.
Find more details at bcftools website:
https://samtools.github.io/bcftools/bcftools.html
"""

import os.path as op
import sys
from JamesLab.apps.base import ActionDispatcher, OptionParser, glob,iglob
from JamesLab.apps.natsort import natsorted
import subprocess
from JamesLab.apps.header import Slurm_header

def main():
    actions = (
        ('NUM_ALT', 'filter number of alternative SNPs'),
        ('Miss_Rate', 'filter missing rate'),
        ('HeterMiss_Rate', 'filter SNPs with high heterozygous and missing rates'),
        ('Bad_Indels', 'remove wrong INDELs'),
        ('MAF', 'filter minor allele frequency'),
        ('Subsampling', 'choose part of samples from vcf'),
)
    p = ActionDispatcher(actions)
    p.dispatch(globals())

def Subsampling(args):
    """
    %prog Subsampling SMs_file vcf_or_vcf.gz
    Subsampling vcf file
    """
    p = OptionParser(Subsampling.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)

    if len(args) == 0:
        sys.exit(not p.print_help())
    SMsfile, vcffile, = args
    
    prefix = vcffile.split('.')[0]
    new_f = prefix + '.subsm.vcf'
    cmd = "bcftools view -S %s %s > %s"%(SMsfile, vcffile, new_f)
    jobfile = '%s.subsm.slurm'%prefix
    f = open(jobfile, 'w')
    header = Slurm_header%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    header += 'module load bcftools\n'
    header += cmd
    f.write(header) 
    print('slurm file %s.subsm.slurm has been created, you can sbatch your job file.'%prefix)

def NUM_ALT(args):
    """
    %prog NUM_ALT vcf_or_vcf.gz
    only retain SNPs with only one ALT    
    """
    p = OptionParser(NUM_ALT.__doc__)
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    
    if len(args) == 0:
        sys.exit(not p.print_help())
    vcffile, = args
    prefix = vcffile.split('.')[0]
    new_f = prefix + '.alt1.vcf'
    cmd = "bcftools view -i 'N_ALT=1' %s > %s"%(vcffile, new_f)
    jobfile = '%s.alt1.slurm'%prefix
    f = open(jobfile, 'w')
    header = Slurm_header%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    header += 'module load bacftools\n'
    header += cmd
    f.write(header) 
    print('slurm file %s.alt1.slurm has been created, you can sbatch your job file.'%prefix)

def Miss_Rate(args):
    """
    %prog Miss_Rate vcf_or_vcf.gz
    Remove SNPs with high missing rate (>0.4 by default)
    """
    p = OptionParser(Miss_Rate.__doc__)
    p.add_option('--missing_rate', default = 0.4, 
        help = 'specify the missing rate cutoff')
    p.add_option('--NS', default = 'NS', choices=('NS', 'NZ'), 
        help = 'specify the tag name of number of nonmissing samples')
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    vcffile, = args
    prefix = vcffile.split('.')[0]
    new_f = prefix + '.missR.vcf'

    subprocess.call('module load bcftools', shell=True)
    child = subprocess.Popen('bcftools query -l %s|wc -l'%vcffile, shell=True, stdout=subprocess.PIPE)
    out = int(child.communicate()[0])
    print('Total %s Samples.'%out)

    cmd = "bcftools view -i '%s/%s > %s' %s > %s\n"%(opts.NS, out, opts.missing_rate, vcffile, new_f)
    jobfile = '%s.missR.slurm'%prefix
    f = open(jobfile, 'w')
    header = Slurm_header%(opts.time, opts.memory, opts.prefix, opts.prefix, opts.prefix)
    header += 'module load bcftools\n'
    header += cmd
    f.write(header)
    print('slurm file %s.missR.slurm has been created, you can sbatch your job file.'%prefix)

def genotypes_count(snp, imputed):
    a1, a2, h, m = snp.count('0/0'), i.count('1/1'), i.count('0/1'), i.count('./.')\
        if imputed=='no' \
        else i.count('0|0'), i.count('1|1'), i.count('0|1'), i.count('.|.')
    return a1, a2, h, m

def HeterMiss_Rate(args):
    """
    %prog vcf
    Remove bad and high heterizygous loci
    """
    p = OptionParser(HeterMiss_Rate.__doc__)
    p.add_option('--h2_rate', default = 0.05,
        help = 'specify the heterozygous rate cutoff')
    p.add_option('--m_rate', default = 0.4, 
        help = 'specify the missing rate cutoff')
    p.add_option('--imputed', default = 'no', choices=('no', 'yes'), 
        help = 'specify the missing rate cutoff')
    p.set_slurm_opts(array=False)
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    vcffile, = args
    prefix = vcffile.split('.')[0]
    new_f = prefix + '.HeteMissR.vcf'
    
    f0 = open(vcffile)
    f1 = open(new_f, 'w')
    for i in f0:
        if i.startswith('#'):
            f1.write(i)
        else:
            a1, a2, h, m = genotypes_count(i, opts.imputed)
            if h < min(a1, a2) and h/float(a1+a2+h) < float(opts.h2_rate) and m/float(a1+a2+h+m) < float(opts.m_rate):
                f1.write(i)
    f0.close()
    f1.close()

def MAF(args):
    """
    %prog maf vcf
    Remove SNPs with rare MAF
    """
    p = OptionParser(HeterMiss_Rate.__doc__)
    p.add_option('--imputed', default = 'no', choices=('no', 'yes'),
        help = 'specify the missing rate cutoff')
    opts, args = p.parse_args(args)
    if len(args) == 0:
        sys.exit(not p.print_help())
    maf, vcffile, = args   
    maf = float(maf)
    
    prefix = vcffile.split('.')[0]
    new_f = prefix + '.maf.vcf'
    
    f0 = open(vcffile)
    f1 = open(new_f, 'w')
    for i in f0:
        if i.startswith('#'):
            f1.write(i)
        else:
            a1, a2, h, m = genotypes_count(i, opts.imputed)
            total = float((a1+a2+h)*2)
            allele_1 = a1*2 + h
            allele_2 = a2*2 + h
            if min(allele_1/total, allele_2/total) > MAF:
                f1.write(i)
    f0.close()
    f1.close()

def Bad_Indels(args):
    pass

if __name__ == "__main__":
    main()