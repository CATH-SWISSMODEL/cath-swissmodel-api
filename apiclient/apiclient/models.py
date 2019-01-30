import json

class SubmitAlignment(object):
    """Represents the data required to submit a job to the SM Alignment API."""

    def __init__(self, *, target_sequence, template_sequence, template_seqres_offset,
                 pdb_id, auth_asym_id, assembly_id=None, project_id=None):
        self.target_sequence = target_sequence
        self.template_sequence = template_sequence
        self.template_seqres_offset = template_seqres_offset
        self.pdb_id = pdb_id
        self.auth_asym_id = auth_asym_id
        self.assembly_id = assembly_id
        self.project_id = project_id

    @classmethod
    def load(cls, infile):
        """Creates a new instance of this model from a JSON filehandle."""
        try:
            data = json.load(infile)
        except Exception as err:
            raise Exception("failed to load {} from json file '{}': {}".format(cls, infile, err))
        if 'meta' in data:
            del data['meta']
        return cls(**data)

    def as_dict(self):
        """Represents the model as a dict (removes optional keys that do not have values)"""
        data = self.__dict__
        data = dict((k, v) for k, v in data.items() if v != None)
        return data


class ConfigFile(object):
    """ Represents the data in the configuration file """

    def __init__(self, *, api_token=None):
        self.api_token = api_token

    @classmethod
    def load(cls, infile):
        """Creates a new instance of this model from a JSON filehandle."""
        data = json.load(infile)
        return cls(**data)

    def as_dict(self):
        """Represents the model as a dict (removes optional keys that do not have values)"""
        data = self.__dict__
        data = dict((k, v) for k, v in data.items() if v != None)
        return data

    def save(self, outfile):
        """Saves this model to a JSON filehandle."""
        json.dump(self.as_dict(), outfile)
