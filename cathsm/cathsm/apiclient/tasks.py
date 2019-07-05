# core

import argparse
import logging
import os
import re
import string
import tempfile
from multiprocessing import Pool

# non-core
import requests
from Bio import SeqIO

# local
from cathsm.apiclient import managers, models, clients, errors

LOG = logging.getLogger(__name__)


def log_br(log=None):
    if not log:
        log = LOG
    log.info('')


def log_hr(log=None):
    if not log:
        log = LOG
    log.info('')
    log.info('-'*80)
    log.info('')


class CathSMSequenceTask:
    """
    Runs the main modelling pipeline for a given query sequence
    """

    GLOBAL_SEQUENCE_COUNT = 0

    def __init__(self, *, seq_id, seq_str, outdir, api1_base, api2_base, api1_user, api2_user, seq_count=None, log=None):
        self.seq_id = seq_id
        self.seq_str = seq_str
        self.outdir = outdir
        self.api1_base = api1_base
        self.api2_base = api2_base
        self.api1_user = api1_user
        self.api2_user = api2_user
        self.seq_count = seq_count
        if not log:
            self.log = LOG

        self.GLOBAL_SEQUENCE_COUNT += 1
        if not seq_count:
            self.seq_count = self.GLOBAL_SEQUENCE_COUNT

    def run(self):
        """
        Processes an individual query sequence
        """

        seq_id = self.seq_id
        seq_str = self.seq_str
        outdir = self.outdir
        seq_count = self.seq_count

        os.chdir(outdir)

        log = logging.getLogger('process_sequence_{}'.format(seq_count))
        fh = logging.FileHandler('process.log')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        log.addHandler(fh)

        log.info("SEQUENCE %s: %s (%s residues)",
                 seq_count, seq_id, len(seq_str))

        char_width = 80
        seq_lines = [seq_str[i:i+char_width]
                     for i in range(0, len(seq_str), char_width)]
        for seq_line in seq_lines:
            log.info("{}".format(seq_line))

        log_br(log)
        log.info("Searching for template structures ... ")

        api1submit = models.SubmitSelectTemplate(
            query_id=seq_id, query_sequence=seq_str)

        api1 = managers.CathSelectTemplateManager(
            base_url=self.api1_base,
            submit_data=api1submit,
            api_user=self.api1_user,
            logger=log,
        )

        api1.run()

        task_uuid = api1.task_uuid

        log_br(log)

        # TODO: abstract the following chunk of hard coded URLs
        # to clients / managers / swagger? ...

        # swagger_app, swagger_client = api1.api_client.get_swagger()
        # hit_operation_id = 'select-template_resolved_hits_read'  # TODO: this is nasty
        # req, resp = swagger_app.op[hit_operation_id](
        #     uuid=api1.task_uuid)
        # req.produce('application/json')
        # hits = swagger_client.request((req, resp)).data

        api1_base = self.api1_base
        headers = {'Authorization': 'Token ' + api1.api_token}

        log.info("Getting resolved hit info ...")
        hits_url = '{api1_base}/api/select-template/{task_uuid}/resolved_hits'.format(
            api1_base=api1_base, task_uuid=task_uuid)
        log.info("GET %s", hits_url)
        resp = requests.get(hits_url, headers=headers)
        resp.raise_for_status()
        hits = resp.json()
        log.info("  ... retrieved %s resolved hits", len(hits))
        log_br(log)

        # hits = managers.GetSelectTemplateHits(task_uuid=api1.task_uuid)
        # hits = api1.funfam_resolved_scan_hits()

        for hit_count, hit in enumerate(hits, 1):

            log_hr(log)

            log.info("SEQUENCE %s, HIT %s [%s]: FunFam '%s': %s",
                     seq_count, hit_count, hit['query_range'], hit['ff_id'], hit['ff_name'])

            log.info("Getting template alignments ...")
            aln_url = '{api1_base}/api/select-template/hit/{hit_uuid}/alignments'.format(
                api1_base=api1_base, hit_uuid=hit['uuid'])
            log.info("GET %s", aln_url)
            resp = requests.get(aln_url, headers=headers)
            resp.raise_for_status()
            alns = resp.json()
            log.info("  ... retrieved %s template alignments", len(alns))
            log_br(log)

            if not alns:
                log.warning("Found no valid template alignments from hit '%s'. This is probably due " + \
                    "to a lack of non-discontinuous CATH domains in the matching FunFam (skipping modelling step).", hit['ff_id'])
                continue

            log_prefix = 'HIT{}'.format(hit_count)
            aln = alns[0]

            log.info("%s: Modelling region against template %s, %s (offset %s) ... ",
                     log_prefix, aln['pdb_id'], aln['auth_asym_id'], aln['template_seqres_offset'])

            log.info("%10s %8s: %s", 'QUERY',
                     hit['query_range'],
                     aln['target_sequence'], )
            log.info("%10s %8s: %s", '{}, {}'.format(aln['pdb_id'], aln['auth_asym_id']),
                     aln['template_seqres_offset'],
                     aln['template_sequence'])
            log_br(log)

            api2submit = models.SubmitAlignment(
                target_sequence=aln['target_sequence'],
                template_sequence=aln['template_sequence'],
                template_seqres_offset=aln['template_seqres_offset'],
                pdb_id=aln['pdb_id'],
                auth_asym_id=aln['auth_asym_id'],
            )

            pdb_out_id = re.sub('[\W]+', '', seq_id)

            api2 = managers.SMAlignmentManager(
                base_url=self.api2_base,
                submit_data=api2submit,
                outfile="{}.pdb".format(pdb_out_id),
                api_user=self.api2_user,
                logger=log,
            )
            api2.run()
            log_br(log)


class CathSMSequenceFileTask:
    """
    Runs the main modelling pipeline for a set of sequences
    """

    def __init__(self, *, infile, outdir, max_workers, api1_base, api2_base, api1_user, api2_user, startseq=1):
        self.infile = infile
        self.outdir = outdir
        self.max_workers = max_workers
        self.startseq = startseq
        self.api1_base = api1_base
        self.api2_base = api2_base
        self.api1_user = api1_user
        self.api2_user = api2_user

    def run(self):

        # defining these here because it makes refactoring a bit easier
        infile = self.infile
        startseq = self.startseq
        outdir = self.outdir
        api1_base = self.api1_base
        api2_base = self.api2_base
        api1_user = self.api1_user
        api2_user = self.api2_user

        LOG.info("Parsing sequences from %s", infile)
        log_hr()
        sequences = []
        for seq in SeqIO.parse(infile, "fasta"):
            LOG.info("SEQUENCE: '%s' (%d residues)",
                     seq.id, len(seq))
            sequences.extend([seq])

        re_safe = re.compile(r'[\W]+', re.UNICODE)
        process_args = []
        for seq_count, seq in enumerate(sequences[startseq-1:], startseq):

            safe_dirname = re_safe.sub('', seq.id)
            process_outdir = os.path.abspath(
                os.path.join(outdir, safe_dirname))

            if not os.path.exists(process_outdir):
                os.makedirs(process_outdir)

            process_args.extend(
                [[seq_count, seq.id, seq.seq, process_outdir, api1_user, api2_user]])

        # TODO: use multiprocessing to get this working in parallel
        # with Pool(max_workers) as p:
        #    p.map(process_sequence, process_args)

        for pargs in process_args:
            seq_count, seq_id, seq_str, outdir, api1_user, api2_user = list(
                pargs)
            seq_task = CathSMSequenceTask(seq_id=seq_id,
                                          seq_str=seq_str,
                                          api1_base=api1_base,
                                          api2_base=api2_base,
                                          api1_user=api1_user,
                                          api2_user=api2_user,
                                          outdir=outdir, )
            seq_task.run()

        LOG.info("DONE")
