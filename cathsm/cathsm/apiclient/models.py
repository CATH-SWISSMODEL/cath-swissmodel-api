import json
import logging

LOG = logging.getLogger(__name__)

class SubmitAlignment(object):
    """Represents the data required to submit a job to the SM Alignment API."""

    def __init__(self, *, target_sequence, template_sequence, template_seqres_offset,
                 pdb_id, auth_asym_id, assembly_id=None, project_id=None, meta=None):

        if not meta:
            meta = {}

        self.target_sequence = target_sequence
        self.template_sequence = template_sequence
        self.template_seqres_offset = template_seqres_offset
        self.pdb_id = pdb_id
        self.auth_asym_id = auth_asym_id
        self.assembly_id = assembly_id
        self.project_id = project_id
        self.meta = meta

    @classmethod
    def load(cls, infile):
        """Creates a new instance of this model from a JSON filehandle."""
        try:
            data = json.load(infile)
        except Exception as err:
            raise Exception("failed to load {} from json file '{}': {}".format(cls, infile, err))
        return cls(**data)

    def as_dict(self, *, remove_meta=True):
        """Represents the model as a dict (removes optional keys that do not have values)"""
        data = self.__dict__
        if remove_meta and 'meta' in data:
            del data['meta']
        data = dict((k, v) for k, v in data.items() if v != None)
        return data
