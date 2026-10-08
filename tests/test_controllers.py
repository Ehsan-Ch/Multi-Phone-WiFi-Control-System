import shlex
import subprocess
import unittest
from unittest.mock import patch, Mock
from phone_controller import PhoneController
from wifi_connection import WiFiADBManager


class ControllerTests(unittest.TestCase):
    def controller(self):
        with patch.object(PhoneController, 'scan_devices'):
            return PhoneController()

    def test_empty_install_does_not_construct_zero_worker_pool(self):
        self.assertEqual(self.controller().install_app_all('example.apk'), [])

    def test_failed_scan_clears_old_devices(self):
        controller = self.controller()
        controller.devices = ['old-device']
        with patch('phone_controller.subprocess.run', side_effect=FileNotFoundError):
            self.assertEqual(controller.scan_devices(), [])
        self.assertEqual(controller.devices, [])

    def test_input_text_is_one_literal_remote_shell_argument(self):
        controller = self.controller()
        text = 'a "quote" & $(echo nope); it\'s `literal`'
        controller.execute_command = Mock()
        controller.input_text('device', text)
        command = controller.execute_command.call_args.args[1]
        self.assertEqual(shlex.split(command), ['input', 'text', text.replace(' ', '%s')])
        controller.execute_all = Mock()
        controller.input_text_all(text)
        self.assertEqual(shlex.split(controller.execute_all.call_args.args[0]),
                         ['input', 'text', text.replace(' ', '%s')])

    def test_wifi_entries_are_excluded_from_usb_setup(self):
        response = subprocess.CompletedProcess([], 0, stdout=(
            'List of devices attached\n'
            'usb123 device usb:1-1 product:test\n'
            '192.168.1.2:5555 device product:test\n'
            'adb-phone._adb-tls-connect._tcp device product:test\n'
            'locked unauthorized usb:1-2\n'))
        with patch('wifi_connection.subprocess.run', return_value=response):
            self.assertEqual(WiFiADBManager().get_usb_devices(), ['usb123'])

    def test_failed_install_is_not_reported_as_success(self):
        response = subprocess.CompletedProcess([], 1, stdout='Success', stderr='failed')
        with patch('phone_controller.subprocess.run', return_value=response):
            self.assertFalse(self.controller().install_app('d', 'a.apk')['success'])


if __name__ == '__main__':
    unittest.main()
