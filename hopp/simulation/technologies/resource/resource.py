from abc import ABCMeta, abstractmethod
import os
import json
import requests
import time
from pathlib import Path
from hopp import ROOT_DIR

class Resource(metaclass=ABCMeta):
    """
    Class to manage resource data for a given lat & lon. If a resource file doesn't exist,
    it is downloaded and saved to 'resource_files' folder. The resource file is then read
    to the appropriate SAM resource data format.
    """
    def __init__(self, lat, lon, year, **kwargs):
        """
        Parameters
        ---------
        lat: float
            The latitude
        lon: float
            The longitude
        year: int
            The year of resource_files data
        """

        self.latitude = lat
        self.longitude = lon
        self.year = year

        self.n_timesteps = 8760

        # generic api settings
        self.interval = str(int(8760/365/24 * 60))
        self.leap_year = 'false'
        self.utc = 'false'
        self.name = 'hybrid-systems'
        self.affiliation = 'NREL'
        self.reason = 'hybrid-analysis'
        self.mailing_list = 'true'
        # paths
        self.path_current = os.path.dirname(os.path.abspath(__file__))
        self.path_resource = os.path.join(ROOT_DIR, 'simulation', 'resource_files')
        self.filename = None #: filepath of resource data file, defaults to None
        
        # update any passed in
        self.__dict__.update(kwargs)

        self._data = dict()

    def check_download_dir(self):
        """Creates directory for the resource file if it does not exist.
        """
        if not isinstance(self.filename,str):
            self.filename = str(self.filename)
        if not os.path.isdir(os.path.dirname(self.filename)):
            os.makedirs(os.path.dirname(self.filename))

    @staticmethod
    def call_api(url, filename):
        """
        Args:
            url (str): The API endpoint to return data from
            filename (str): The filename where data should be written
        
        Returns:
            True if downloaded file successfully, False if encountered error in downloading
            
        """

        n_tries = 0
        success = False
        while n_tries < 5:

            try:
                r = requests.get(url)
                if r:
                    localfile = open(filename, mode='w+')
                    txt = r.text.replace("(Â°C)","(C)").replace("(Â°)","(deg)")
                    localfile.write(txt)
                    localfile.close()
                    if os.path.isfile(filename):
                        success = True
                        break
                elif r.status_code == 400 or r.status_code == 403:
                    print(r.url)
                    err = r.text
                    text_json = json.loads(r.text)
                    if 'errors' in text_json.keys():
                        err = text_json['errors']
                    raise requests.exceptions.HTTPError(err)
                elif r.status_code == 404:
                    print(filename)
                    raise requests.exceptions.HTTPError
                elif r.status_code == 429:
                    raise RuntimeError("Maximum API request rate exceeded!")
                else:
                    n_tries += 1 # Won't repeat endlessly (and exceed request limit) if API returns unexpected code
            except requests.exceptions.Timeout:
                time.sleep(0.2)
                n_tries += 1

        return success

    @abstractmethod
    def download_resource(self):
        """Download resource for given lat/lon"""

    @abstractmethod
    def format_data(self):
        """Reads data from file and formats it for use in SAM"""

    @property
    def data(self):
        """Get data as dictionary formatted for SAM"""
        return self._data

    @data.setter
    @abstractmethod
    def data(self, data_dict):
        """Sets data from dictionary"""
