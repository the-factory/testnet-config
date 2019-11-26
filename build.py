#!/usr/bin/env python3

import os
import shutil

TEMPLATE_DIR = './templates'
DEST_DIR = './_build'

PEER_CONFIG_NAMES = ['harvesting']
API_CONFIG_NAMES = ['database', 'messaging', 'pt']
SHARED_CONFIG_NAMES = ['inflation', 'network', 'task', 'timesync', 'user']

PEER_EXTENSION_NAMES = ['harvesting', 'syncsource']
API_EXTENSION_NAMES = ['filespooling', 'partialtransaction']
BROKER_EXTENSION_NAMES = ['addressextraction', 'mongo', 'zeromq', 'hashcache']
SHARED_EXTENSION_NAMES = [
    'diagnostics', 'hashcache', 'nodediscovery', 'packetserver', 'pluginhandlers', 'sync', 'timesync', 'transactionsink', 'unbondedpruning'
]


def copyWithReplacements(inputPath, outputPath, replacements):
    with open(inputPath, 'r') as inputFile:
        with open(outputPath, 'w') as outputFile:
            for line in inputFile:
                for replacement in replacements:
                    key = replacement[0]
                    value = replacement[1]
                    if line.startswith(key + ' ='):
                        line = '{0} = {1}\n'.format(key, value)

                outputFile.write(line)


def copyLoggingProperties(topologyName, name):
    inputPath = os.path.join(TEMPLATE_DIR, 'config-logging.properties')
    outputPath = os.path.join(DEST_DIR, topologyName, 'config-logging-{0}.properties'.format(name))
    replacements = [('filePattern', 'catapult_{0}%4N.log'.format(name))]
    copyWithReplacements(inputPath, outputPath, replacements)


def copyExtensionsProperties(topologyName, name, extensions):
    inputPath = os.path.join(TEMPLATE_DIR, 'config-extensions.properties')
    outputPath = os.path.join(DEST_DIR, topologyName, 'config-extensions-{0}.properties'.format(name))
    replacements = [('extension.{0}'.format(extension), 'true') for extension in extensions]
    copyWithReplacements(inputPath, outputPath, replacements)


def buildTopologyConfiguration(topologyName, settings):
    # server
    copyLoggingProperties(topologyName, 'server')
    copyExtensionsProperties(topologyName, 'server', settings['serverExtensionNames'])

    # recovery
    copyLoggingProperties(topologyName, 'recovery')
    copyExtensionsProperties(topologyName, 'recovery', settings['recoveryExtensionNames'])

    # broker (optional)
    if settings['brokerExtensionNames']:
        copyLoggingProperties(topologyName, 'broker')
        copyExtensionsProperties(topologyName, 'broker', settings['brokerExtensionNames'])

    # node
    copyWithReplacements(
        os.path.join(TEMPLATE_DIR, 'config-node.properties'),
        os.path.join(DEST_DIR, topologyName, 'config-node.properties'),
        [
            ('enableSingleThreadPool', 'false' if settings['brokerExtensionNames'] else 'true'),
            ('enableAutoSyncCleanup', 'false' if settings['brokerExtensionNames'] else 'true'),
            ('roles', settings['roles'])
        ])

    # copy simple files
    for name in settings['simpleConfigNames']:
        filename = 'config-{0}.properties'.format(name)
        inputPath = os.path.join(TEMPLATE_DIR, filename)
        outputPath = os.path.join(DEST_DIR, topologyName, filename)
        shutil.copy(inputPath, outputPath)


def prepareDestination():
    os.mkdir(DEST_DIR)
    for topologyName in ['peer', 'api', 'dual']:
        os.mkdir(os.path.join(DEST_DIR, topologyName))


prepareDestination()

buildTopologyConfiguration('peer', {
    'serverExtensionNames': PEER_EXTENSION_NAMES + SHARED_EXTENSION_NAMES,
    'brokerExtensionNames': [],
    'recoveryExtensionNames': ['hashcache'],
    'roles': 'Peer',
    'simpleConfigNames': PEER_CONFIG_NAMES + SHARED_CONFIG_NAMES
})

buildTopologyConfiguration('api', {
    'serverExtensionNames': API_EXTENSION_NAMES + SHARED_EXTENSION_NAMES,
    'brokerExtensionNames': BROKER_EXTENSION_NAMES,
    'recoveryExtensionNames': BROKER_EXTENSION_NAMES,
    'roles': 'Api',
    'simpleConfigNames': API_CONFIG_NAMES + SHARED_CONFIG_NAMES
})

buildTopologyConfiguration('dual', {
    'serverExtensionNames': PEER_EXTENSION_NAMES + API_EXTENSION_NAMES + SHARED_EXTENSION_NAMES,
    'brokerExtensionNames': BROKER_EXTENSION_NAMES,
    'recoveryExtensionNames': BROKER_EXTENSION_NAMES,
    'roles': 'Api,Peer',
    'simpleConfigNames': PEER_CONFIG_NAMES + API_CONFIG_NAMES + SHARED_CONFIG_NAMES
})
