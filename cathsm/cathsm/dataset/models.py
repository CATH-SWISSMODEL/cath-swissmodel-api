# core
import json
import logging
import os
import re

# non-core
from cathpy.seqio import Align
from cathpy.error import NoMatchesError

# local
import cathsm.dataset.errors as err

LOG = logging.getLogger(__name__)

FUNFAM_BASE_PATH = '/cath/data/v4_2_0/funfam/families/'

class Domain(object):
    """Represents a protein domain."""
    def __init__(self, *, domain_id, seqres_start, seqres_stop, pdb_start, pdb_stop, seq=None):
        assert(domain_id)
        self.domain_id = domain_id
        self.seqres_start = seqres_start
        self.seqres_stop = seqres_stop
        self.pdb_start = pdb_start
        self.pdb_stop = pdb_stop
        self.seq = seq

class Funfam(object):
    """Represents a CATH Functional Family: a collection of domains sharing similar functions."""

    funfam_base_path = FUNFAM_BASE_PATH

    def __init__(self, *, funfam_id):
        
        sfam_id, cluster_type, ff_num = funfam_id.split('-')
        self.funfam_id = funfam_id
        funfam_sto_fname = '{}.reduced.sto'.format(funfam_id)
        self.funfam_sto_path = os.path.join(self.funfam_base_path, sfam_id, funfam_sto_fname)
        self.funfam_hmm_path = self.funfam_sto_path + '.hmm'    

        self.funfam_align = Align.new_from_stockholm(self.funfam_sto_path)
    
    def new_domain_from_seq(self, seq):
        re_pdb_seg = re.compile(r'(\S{4});\s+(\S):(-?[0-9]+[A-Z]?)-(-?[0-9]+[A-Z]?)')

        if len(seq.segs) > 1:
            raise err.NoDiscontinuousDomainsError("Error: not set up to deal with discontinuous domains: {}".format(seq.id))
        
        firstseg = seq.segs[0]
        
        pdb_code = None
        auth_asym_id = None
        pdb_start = None
        pdb_stop = None

        if 'DR_CATH' in seq.meta:
            cath_ref = seq.meta['DR_CATH']
            m = re_pdb_seg.match(cath_ref)
            if not m:
                raise Exception("Error: failed to parse PDB chopping info '{}'".format(cath_ref))    
            pdb_code, auth_asym_id, pdb_start, pdb_stop = m.groups()

        d = Domain(
            domain_id=seq.accession,
            seqres_start=firstseg.start,
            seqres_stop=firstseg.stop,
            pdb_start=pdb_start,
            pdb_stop=pdb_stop,
            seq=seq.seq, )
    
        return d
    
    def get_domain(self, domain_id):
        aln = self.funfam_align
        seq = aln.find_seq_by_id(domain_id)
        return self.new_domain_from_seq(seq)
        
    def get_cath_domains(self):
        aln = self.funfam_align
        cath_seqs = [s for s in aln.seqs if s.is_cath_domain]
        cath_domains = []
        for seq in cath_seqs:
            d = self.new_domain_from_seq(seq)
            cath_domains.extend([d])
        return cath_domains
            

class DomainModel(object):
    """Represents a predicted 3D model for a region of UniProtKB sequence"""

    def __init__(self, *, start, end, template, identity, qmean_norm=None, qmean_z=None, dope_score=None):
        self.start = start
        self.end = end
        self.template = template
        self.identity = identity
        self.qmean_norm = qmean_norm
        self.qmean_z = qmean_z
        self.dope_score = dope_score

    @classmethod
    def new_from_cath_model_pdb(cls, model_path):
        model_basename = os.path.basename(model_path)

        # A0A0A6YYL3,92-385
        m = re.match(r'^(\w+),(\d+)-(\d+)$', model_basename)
        if not m:
            raise err.CannotParseModelFilenameError('failed to parse model basename {}'.format(model_basename))
        uniprot_id, start, end = m.groups()

        # REMARK   6 MODELLER OBJECTIVE FUNCTION:      2421.6941
        # REMARK   6 MODELLER BEST TEMPLATE % SEQ ID:  91.389
        # REMARK   6 SEQUENCE: model
        # REMARK   6 ALIGNMENT: alignment.pir
        # REMARK   6 SCRIPT: script.py
        # REMARK   6 DOPE score: -77588.44531
        # REMARK   6 GA341 score: 1.00000
        # REMARK   6 Normalized DOPE score: -1.45177
        # REMARK   6 TEMPLATE: 5b1aN00 2:N - 514:N MODELS 1: - 511: AT 91.4%

        re_identity = re.compile(r'SEQ ID:\s+([0-9.]+)')
        re_template = re.compile(r'TEMPLATE:\s+(\w+)')
        re_dope = re.compile(r'Normalized DOPE score:\s+([\-0-9.]+)')

        identity = None
        template = None
        dope_score = None
        with open(model_path) as io:
            seen_remark = False
            for line in io:
                if line.startswith('REMARK'):
                    seen_remark = True
                else:
                    # stop parsing after the REMARK block finishes
                    # HACK: (ish) assumes all the REMARK lines are together
                    if seen_remark: 
                        break
                    else: 
                        continue

                m = re_identity.search(line)
                if m:
                    identity = m[1]
                m = re_template.search(line)
                if m:
                    template = m[1]
                m = re_dope.search(line)
                if m:
                    dope_score = m[1]

        if not dope_score:
            raise Exception('failed to parse dope score from file {}'.format(model_path)) 
        if not template:
            raise Exception('failed to parse template from file {}'.format(model_path)) 
        if not identity:
            raise Exception('failed to parse identity from file {}'.format(model_path)) 

        model = cls(start=start, end=end, dope_score=dope_score, template=template, identity=identity)

        LOG.debug("MODEL: {} start={} end={} dope={} template={} identity={}".format(
            uniprot_id, model.start, model.end, model.dope_score, model.template, model.identity
        ))
        return model

class Uniprot(object):
    """Represents a set of UniProtKB sequence with SM / CATH models"""

    def __init__(self, *, uniprot_id, sequence_md5, sm_models=None, cath_models=None):
        if not sm_models:
            sm_models = []
        if not cath_models:
            cath_models = []

        self.uniprot_id = uniprot_id
        self.sequence_md5 = sequence_md5
        self.sm_models = sm_models
        self.cath_models = cath_models

class OrgDataFile(object):
    """Represents a set of sequence annotations for a given organism"""

    def __init__(self, *, path_name, uniprot_release, organism, taxon_id, sequences):
        self.path_name = path_name
        self.uniprot_release = uniprot_release
        self.organism = organism
        self.taxon_id = taxon_id
        self.sequences = sequences

    def filter_sequences_by_any_sm_model(self, *, min_score, max_score):
        seqs = [s for s in self.sequences 
                if any(m.qmean_z >= min_score and m.qmean_z <= max_score for m in s.sm_models)]
        return seqs

    @classmethod
    def new_from_sm_dump(cls, f):

        uniprot_data = None
        sequences = []
        with open(f) as io:
            data = json.load(io)
            
            for u_id, u_data in data['uniprot_ids'].items():
                models = [
                    DomainModel(
                        start=m['from'], 
                        end=m['to'], 
                        qmean_norm=m['qmean_norm'],
                        qmean_z=m['qmean_z'],
                        template=m['template'],
                        identity=m['identity'],
                    ) for m in u_data['smr_models']]
                
                uniprot_entry = Uniprot(
                    uniprot_id=u_id, 
                    sequence_md5=u_data['sequence_md5'], 
                    sm_models=models,
                )
                
                sequences.extend([uniprot_entry])
        
            uniprot_data = cls(
                path_name = f,
                taxon_id = int(data['info']['taxid']),
                organism = str(data['info']['organism']),
                uniprot_release = data['info']['uniprot_release'],
                sequences = sequences,
            )
        
        return uniprot_data
