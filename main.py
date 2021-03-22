# -*- coding: utf-8 -*-
import os
import argparse
import configparser
from pathlib import Path
from slack_export_data import SlackExportData
import tempfile
import shutil
import re


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
                    if('root' in message):
                        if ('files' in message['root']):
                            fileinfos = []
                            for file in message['root']['files']:
                                if (file['mode'] == 'hosted'):
                                    fileinfos.append(file)
                                else:
                                    hostedFile = self.getHostedFileInfo(
                                        file['id'])
                                    if (hostedFile is not None):
                                        fileinfos.append(hostedFile)
                            message['root']['text'] += "\n---\n添付ファイル\n"
                            for fileinfo in fileinfos:
                                url = str(fileinfo['url_private']).replace(
                                    '\\', '').split('?')[0]
                                message['root']['text'] += "<{}|{}>\n".format(url,url)
                            del message['root']['files']

                            if ('upload' in message['root']):
                                del message['root']['upload']

                    if ('files' in message):
                        fileinfos = []
                        for file in message['files']:
                            if (file['mode'] == 'hosted'):
                                fileinfos.append(file)
                            else:
                                hostedFile = self.getHostedFileInfo(file['id'])
                                if (hostedFile is not None):
                                    fileinfos.append(hostedFile)
                        message['text'] += "\n---\n添付ファイル\n"
                        for fileinfo in fileinfos:
                            url = str(fileinfo['url_private']).replace(
                                '\\', '').split('?')[0]
                            message['text'] += "<{}|{}>\n".format(url,url)
                        del message['files']

                        if ('upload' in message):
                            del message['upload']

        print('Complete : reconstruncting export data..\n\n')

    def replaceFileInfo(self):
        print('Finding message which has file hidden by limit..')
        for channel in self.export_data.channelDirectories:
            print('Channel : {} ..'.format(channel.path.parts[-1]))
            for message_file in channel.messages:
                for message in message_file.json:
                    if('root' in message):
                        if ('files' in message['root']):
                            fileinfos = []
                            for file in message['root']['files']:
                                if (file['mode'] == 'hosted'):
                                    fileinfos.append(file)
                                else:
                                    hostedFile = self.getHostedFileInfo(
                                        file['id'])
                                    if (hostedFile is not None):
                                        fileinfos.append(hostedFile)
                            message['root']['files'] = fileinfos

                    if ('files' in message):
                        fileinfos = []
                        for file in message['files']:
                            if (file['mode'] == 'hosted'):
                                fileinfos.append(file)
                            else:
                                hostedFile = self.getHostedFileInfo(file['id'])
                                if (hostedFile is not None):
                                    fileinfos.append(hostedFile)
                        message['files'] = fileinfos
        print('Complete : replaceing export data..\n\n')

    def replaceUserName(self):
        print('Replaceing user name..')
        for channel in self.export_data.channelDirectories:
            print('Channel : {} ..'.format(channel.path.parts[-1]))
            for message_file in channel.messages:
                for message in message_file.json:
                    if('attachments' in message):
                        for attachment in message['attachments']:
                            if ('text' in attachment):
                                text = str(attachment['text'])
                                results = re.findall(
                                    r"\<@[0-9,A-Z]{9,11}\>", text)
                                for result in results:
                                    userinfo = self.export_data.users.getUserByID(
                                        result[2:-1])
                                    if userinfo is not None:
                                        if 'real_name' in userinfo:
                                            text = text.replace(
                                                result, " *@{}* ".format(userinfo['real_name']))
                                        else:
                                            text = text.replace(
                                                result, " *@{}* ".format(userinfo['name']))
                                if len(results) >= 1:
                                    attachment['text'] = text

                    if('root' in message):
                        if ('text' in message['root']):
                            text = str(message['root']['text'])
                            results = re.findall(r"\<@[0-9,A-Z]{9,11}\>", text)
                            for result in results:
                                userinfo = self.export_data.users.getUserByID(
                                    result[2:-1])
                                if userinfo is not None:
                                    if 'real_name' in userinfo:
                                        text = text.replace(
                                            result, " *@{}* ".format(userinfo['real_name']))
                                    else:
                                        text = text.replace(
                                            result, " *@{}* ".format(userinfo['name']))
                            if len(results) >= 1:
                                message['root']['text'] = text

                    if ('text' in message):
                        text = str(message['text'])
                        results = re.findall(r"\<@[0-9,A-Z]{9,11}\>", text)
                        for result in results:
                            userinfo = self.export_data.users.getUserByID(
                                result[2:-1])
                            if userinfo is not None:
                                if 'real_name' in userinfo:
                                    text = text.replace(
                                        result, " *@{}* ".format(userinfo['real_name']))
                                else:
                                    text = text.replace(
                                        result, " *@{}* ".format(userinfo['name']))
                        if len(results) >= 1:
                            message['text'] = text
        print('Complete : replaceing user name..\n\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('output')
    parser.add_argument('--replace', action="store_true")
    parser.add_argument('--reconstruct', action="store_true")
    parser.add_argument('--username', action="store_true")

    args = parser.parse_args()
    reconstructor = SlackExportDataReconstructor(args.config)
    reconstructor.export_data.printFileStructure()
    reconstructor.export_data.getNumberOfMessage()

    if (args.username):
        reconstructor.replaceUserName()

    if (args.reconstruct):
        reconstructor.reconstructFileInfo()
        reconstructor.export_data.getArchiveJSONData(args.output)
    elif (args.replace):
        reconstructor.replaceFileInfo()
        reconstructor.export_data.getArchiveJSONData(args.output)
