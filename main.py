# -*- coding: utf-8 -*-
import os
import argparse
import configparser
from pathlib import Path
from slack_export_data import SlackExportData
import tempfile
import shutil

class SlackExportDataReconstructor:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.read(config_file)

        self.export_data = None
        self.reference_data = []

        for export_data in self.config['export data']:
            print('Unpacking {} ...'.format(export_data))
            with tempfile.TemporaryDirectory() as tempDir:
                shutil.unpack_archive(export_data, extract_dir=tempDir)
                self.export_data = SlackExportData(tempDir)

        for reference_data_file in self.config['reference data']:
            print('Unpacking {} ...'.format(reference_data_file))
            with tempfile.TemporaryDirectory() as tempDir:
                shutil.unpack_archive(reference_data_file, extract_dir=tempDir)
                self.reference_data.append(SlackExportData(tempDir))

        print('Initialized.')

    def getHostedFileInfo(self, id):
        for reference in self.reference_data:
            file = reference.getHostedFileInfoByFileID(id)
            if (file is not None):
                return file
        return None

    def reconstructFileInfo(self):
        print('Finding message which has file hidden by limit..')
        for channel in self.export_data.channelDirectories:
            print('Channel : {} ..'.format(channel.path.parts[-1]))
            for message_file in channel.messages:
                for message in message_file.json:
                    if ('files' in message):
                        fileinfos = []
                        for file in message['files']:
                            if (file['mode'] == 'hosted'):
                                fileinfos.append(file)
                            else:
                                hostedFile = self.getHostedFileInfo(file['id'])
                                if (hostedFile is not None):
                                    fileinfos.append(hostedFile)
                        message['text'] += "\n---\n```\n添付ファイル\n"
                        for fileinfo in fileinfos:
                            url = str(fileinfo['url_private']).replace('\\','').split('?')[0]
                            message['text'] += "- {}\n".format(url)
                        message['text'] +="```"
                        del message['files']

                        if ('upload' in message):
                            del message['upload']
        print('Complete : reconstruncting export data..\n\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    args = parser.parse_args()
    reconstructor = SlackExportDataReconstructor(args.config)
    reconstructor.reconstructFileInfo()
    reconstructor.export_data.printFileStructure()
    reconstructor.export_data.getArchiveJSONData('test')
    reconstructor.export_data.getNumberOfMessage()
