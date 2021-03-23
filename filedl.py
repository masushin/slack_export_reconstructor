# -*- coding: utf-8 -*-
import os
import argparse
import configparser
from pathlib import Path
from slack_export_data import SlackExportData
import tempfile
import shutil
import re

import urllib.request
import time
import datetime
import pyexiv2

class SlackFileDownloader:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.read(config_file)

        self.export_data = None

        for export_data in self.config['export data']:
            print('Unpacking {} ...'.format(export_data))
            with tempfile.TemporaryDirectory() as tempDir:
                shutil.unpack_archive(export_data, extract_dir=tempDir)
                self.export_data = SlackExportData(tempDir)

        print('Initialized.')

    def download(self, target_path):
        print("Create target directory .. : {}".format(target_path))

        if not target_path.exists():
            target_path.mkdir()

        print("Downloading files ..")
        for chdir in self.export_data.channelDirectories:
            for targetChName in self.config['channel']:
                if targetChName == chdir.channelDirName:
                    dlpath = Path(target_path/targetChName)
                    if not dlpath.exists():
                        dlpath.mkdir()
                    print(dlpath)
                    for message in chdir.messages:
                        for block in message:
                            if 'files' in block:
                                for file in block['files']:
                                    if 'image/' in file['mimetype']:
                                        filedate = datetime.datetime.fromtimestamp(file['timestamp'])
                                        filename = dlpath/"{}.{}".format(file['id'],file['filetype'])
                                        if not filename.exists():
                                            url = file['url_private_download']
                                            print("Downloading {} : {}..".format(filedate, filename))
                                            try:
                                                opendata = urllib.request.urlopen(url).read()
                                                with open(filename,mode="wb") as f:
                                                    f.write(opendata)
                                            except:
                                                print("Download error ..")
                                                time.sleep(1)
                                                continue

                                            try:
                                                image = pyexiv2.Image(str(filename))
                                                image.modify_exif({'Exif.Image.DateTimeOriginal':"{:04d}:{:02d}:{:02d} {:02d}:{:02d}:{:02d}".format(filedate.year,filedate.month,filedate.day,filedate.hour,filedate.minute,filedate.second)})
                                                image.modify_exif({'Exif.Image.DateTime':"{:04d}:{:02d}:{:02d} {:02d}:{:02d}:{:02d}".format(filedate.year,filedate.month,filedate.day,filedate.hour,filedate.minute,filedate.second)})
                                                image.close()
                                            except:
                                                print("Exif error ..")
                                                continue
                                            os.utime(filename,(file['timestamp'],file['timestamp']))

                                    if 'video/' in file['mimetype']:
                                        filedate = datetime.datetime.fromtimestamp(file['timestamp'])
                                        filename = dlpath/"{}.{}".format(file['id'],file['filetype'])
                                        if not filename.exists():
                                            url = file['url_private_download']
                                            print("Downloading {} : {}..".format(filedate, filename))
                                            try:
                                                opendata = urllib.request.urlopen(url).read()
                                                with open(filename,mode="wb") as f:
                                                    f.write(opendata)
                                            except:
                                                print("Download error ..")
                                                time.sleep(1)
                                                continue
                                            os.utime(filename,(file['timestamp'],file['timestamp']))
                                            time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('output')

    args = parser.parse_args()
    downloader = SlackFileDownloader(args.config)

    for ch in downloader.export_data.channelDirectories:
        print(ch.channelDirName)

    downloader.download(Path(args.output))


