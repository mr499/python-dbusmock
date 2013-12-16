'''ofonod D-BUS mock template'''

# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 3 of the License, or (at your option) any
# later version.  See http://www.gnu.org/copyleft/lgpl.html for the full text
# of the license.

__author__ = 'Martin Pitt'
__email__ = 'martin.pitt@ubuntu.com'
__copyright__ = '(c) 2013 Canonical Ltd.'
__license__ = 'LGPL 3+'


import dbus

import dbusmock

BUS_NAME = 'org.ofono'
MAIN_OBJ = '/'
MAIN_IFACE = 'org.ofono.Manager'
SYSTEM_BUS = True

NOT_IMPLEMENTED = 'raise dbus.exceptions.DBusException("org.ofono.Error.NotImplemented")'


#  interface org.ofono.Manager {
#    methods:
#      GetModems(out a(oa{sv}) modems);
#    signals:
#      ModemAdded(o path,
#                 a{sv} properties);
#      ModemRemoved(o path);
#  };

def load(mock, parameters):
    mock.modems = []  # object paths
    mock.AddMethod(MAIN_IFACE, 'GetModems', '', 'a(oa{sv})',
                   'ret = [(m, objects[m].GetAll("org.ofono.Modem")) for m in self.modems]')

    if not parameters.get('no_modem', False):
        mock.AddModem(parameters.get('ModemName', 'ril_0'), {})


#  interface org.ofono.Modem {
#    methods:
#      GetProperties(out a{sv} properties);
#      SetProperty(in  s property,
#                  in  v value);
#    signals:
#      PropertyChanged(s name,
#                      v value);
#  };

@dbus.service.method(dbusmock.MOCK_IFACE,
                     in_signature='sa{sv}', out_signature='s')
def AddModem(self, name, properties):
    '''Convenience method to add a modem

    You have to specify a device name which must be a valid part of an object
    path, e. g. "mock_ac". For future extensions you can specify a "properties"
    array, but no extra properties are supported for now.

    Returns the new object path.
    '''
    path = '/' + name
    self.AddObject(path,
                   'org.ofono.Modem',
                   {
                       'Online': dbus.Boolean(True, variant_level=1),
                       'Powered': dbus.Boolean(True, variant_level=1),
                       'Lockdown': dbus.Boolean(False, variant_level=1),
                       'Emergency': dbus.Boolean(False, variant_level=1),
                       'Manufacturer': dbus.String('Fakesys', variant_level=1),
                       'Model': dbus.String('Mock Modem', variant_level=1),
                       'Revision': dbus.String('0815.42', variant_level=1),
                       'Type': dbus.String('hardware', variant_level=1),
                       'Interfaces': ['org.ofono.CallVolume',
                                      #'org.ofono.MessageManager',
                                      #'org.ofono.NetworkRegistration',
                                      #'org.ofono.ConnectionManager',
                                      #'org.ofono.NetworkTime',
                                      #'org.ofono.SimManager'
                                      'org.ofono.VoiceCallManager'
                                     ],
                       #'Features': ['sms', 'net', 'gprs', 'sim']
                       'Features': ['gprs'],
                   },
                   [
                       ('GetProperties', '', 'a{sv}', 'ret = self.GetAll("org.ofono.Modem")'),
                       ('SetProperty', 'sv', '', 'self.Set("org.ofono.Modem", args[0], args[1]); '
                                                 'self.EmitSignal("org.ofono.Modem", "PropertyChanged", "sv", [args[0], args[1]])'),
                   ]
                  )
    obj = dbusmock.mockobject.objects[path]
    add_voice_call_api(obj)
    self.modems.append(path)
    self.EmitSignal(MAIN_IFACE, 'ModemAdded', 'oa{sv}', [path, obj.GetProperties()])
    return path

#  interface org.ofono.VoiceCallManager {
#    methods:
#      GetProperties(out a{sv} properties);
#      Dial(in  s number,
#           in  s hide_callerid,
#           out o path);
#      Transfer();
#      SwapCalls();
#      ReleaseAndAnswer();
#      ReleaseAndSwap();
#      HoldAndAnswer();
#      HangupAll();
#      PrivateChat(in  o call,
#                  out ao calls);
#      CreateMultiparty(out o calls);
#      HangupMultiparty();
#      SendTones(in  s SendTones);
#      GetCalls(out a(oa{sv}) calls_with_properties);
#    signals:
#      Forwarded(s type);
#      BarringActive(s type);
#      PropertyChanged(s name,
#                      v value);
#      CallAdded(o path,
#                a{sv} properties);
#      CallRemoved(o path);
#  };


def add_voice_call_api(mock):
    '''Add org.ofono.VoiceCallManager API to a mock'''

    # also add an emergency number which is not a real one, in case one runs a
    # test case against a production ofono :-)
    mock.AddProperty('org.ofono.VoiceCallManager', 'EmergencyNumbers', ['911', '13373'])

    mock.calls = []  # object paths

    mock.AddMethods('org.ofono.VoiceCallManager', [
        ('GetProperties', '', 'a{sv}', 'ret = self.GetAll("org.ofono.VoiceCallManager")'),
        ('Transfer', '', '', ''),
        ('SwapCalls', '', '', ''),
        ('ReleaseAndAnswer', '', '', ''),
        ('ReleaseAndSwap', '', '', ''),
        ('HoldAndAnswer', '', '', ''),
        ('SendTones', 's', '', ''),
        ('PrivateChat', 'o', 'ao', NOT_IMPLEMENTED),
        ('CreateMultiparty', '', 'o', NOT_IMPLEMENTED),
        ('HangupMultiparty', '', '', NOT_IMPLEMENTED),
        ('GetCalls', '', 'a(oa{sv})', 'ret = [(c, objects[c].GetAll("org.ofono.VoiceCall")) for c in self.calls]')
    ])


@dbus.service.method('org.ofono.VoiceCallManager',
                     in_signature='ss', out_signature='s')
def Dial(self, number, hide_callerid):
    path = self._object_path + '/voicecall%02i' % (len(self.calls) + 1)
    self.AddObject(path, 'org.ofono.VoiceCall',
                   {
                       'State': dbus.String('dialing', variant_level=1),
                       'LineIdentification': dbus.String(number, variant_level=1),
                       'Name': dbus.String('', variant_level=1),
                       'Multiparty': dbus.Boolean(False, variant_level=1),
                       'Multiparty': dbus.Boolean(False, variant_level=1),
                       'RemoteHeld': dbus.Boolean(False, variant_level=1),
                       'RemoteMultiparty': dbus.Boolean(False, variant_level=1),
                       'Emergency': dbus.Boolean(False, variant_level=1),
                   },
                   [
                       ('GetProperties', '', 'a{sv}', 'ret = self.GetAll("org.ofono.VoiceCall")'),
                       ('Deflect', 's', '', NOT_IMPLEMENTED),
                       ('Hangup', '', '', 'self.parent.calls.remove(self._object_path);'
                        'self.parent.RemoveObject(self._object_path);'
                        'self.EmitSignal("org.ofono.VoiceCallManager", "CallRemoved", "o", [self._object_path])'),
                       ('Answer', '', '', NOT_IMPLEMENTED),
                   ]
                  )
    obj = dbusmock.mockobject.objects[path]
    obj.parent = self
    self.calls.append(path)
    self.EmitSignal('org.ofono.VoiceCallManager', 'CallAdded', 'oa{sv}',
                    [path, obj.GetProperties()])
    return path


@dbus.service.method('org.ofono.VoiceCallManager',
                     in_signature='', out_signature='')
def HangupAll(self):
    print('XXX HangupAll', self.calls)
    for c in list(self.calls):  # needs a copy
        dbusmock.mockobject.objects[c].Hangup()
    assert self.calls == []

# unimplemented Modem object interfaces:
#
#  interface org.ofono.SimManager {
#    methods:
#      GetProperties(out a{sv} properties);
#      SetProperty(in  s property,
#                  in  v value);
#      ChangePin(in  s type,
#                in  s oldpin,
#                in  s newpin);
#      EnterPin(in  s type,
#               in  s pin);
#      ResetPin(in  s type,
#               in  s puk,
#               in  s newpin);
#      LockPin(in  s type,
#              in  s pin);
#      UnlockPin(in  s type,
#                in  s pin);
#      GetIcon(in  y id,
#              out ay icon);
#    signals:
#      PropertyChanged(s name,
#                      v value);
#  };
#  interface org.ofono.NetworkTime {
#    methods:
#      GetNetworkTime(out a{sv} time);
#    signals:
#      NetworkTimeChanged(a{sv} time);
#    properties:
#  };
#  interface org.ofono.ConnectionManager {
#    methods:
#      GetProperties(out a{sv} properties);
#      SetProperty(in  s property,
#                  in  v value);
#      AddContext(in  s type,
#                 out o path);
#      RemoveContext(in  o path);
#      DeactivateAll();
#      GetContexts(out a(oa{sv}) contexts_with_properties);
#    signals:
#      PropertyChanged(s name,
#                      v value);
#      ContextAdded(o path,
#                   v properties);
#      ContextRemoved(o path);
#  };
#  interface org.ofono.NetworkRegistration {
#    methods:
#      GetProperties(out a{sv} properties);
#      Register();
#      GetOperators(out a(oa{sv}) operators_with_properties);
#      Scan(out a(oa{sv}) operators_with_properties);
#    signals:
#      PropertyChanged(s name,
#                      v value);
#  };
#  interface org.ofono.MessageManager {
#    methods:
#      GetProperties(out a{sv} properties);
#      SetProperty(in  s property,
#                  in  v value);
#      SendMessage(in  s to,
#                  in  s text,
#                  out o path);
#      GetMessages(out a(oa{sv}) messages);
#    signals:
#      PropertyChanged(s name,
#                      v value);
#      IncomingMessage(s message,
#                      a{sv} info);
#      ImmediateMessage(s message,
#                       a{sv} info);
#      MessageAdded(o path,
#                   a{sv} properties);
#      MessageRemoved(o path);
#  };
#  interface org.ofono.CallVolume {
#    methods:
#      GetProperties(out a{sv} properties);
#      SetProperty(in  s property,
#                  in  v value);
#    signals:
#      PropertyChanged(s property,
#                      v value);
#  };
