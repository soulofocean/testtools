#!/usr/bin/env python
# coding=UTF-8
import datetime
import random

# 设备初始化参数
Attribute_initialization = {
    "mac_list": ['58:FC:DB:DA:53:80', '58:FC:DB:DA:53:81'],
    "DeviceFacturer": 1005,
    "DeviceType": 2009,
    "subDeviceType": 3010,
    "_type": 0,
    "_name": 'dog door',
    "_manufacturer": 'HDIOT',
    "_ip": "192.168.0.235",
    "_mask": '255.255.255.0',
    "_version": '1.0.01',
    "_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S').encode('utf-8'),
    "_appVersionInfo": 'appVersionInfo.8.8.8',
    "_fileServerUrl": 'http://192.168.10.1/noexist',
    "_ntpServer": '4.4.4.4',
    "_openDuration": 10,
    "_current_openDuration": 10,
    "_alarmTimeout": 20,
    "_startTime": '1988-08-08',
    "_endTime": '2888-08-08',
    "_UserType": '',
    "_userID": '',
    "_CredenceType": 2,
    "_credenceNo": '12345678',
    "_State": 0,

    "SPECIAL_ITEM": {
        "_State": {
            "init_value": 0,
            "wait_time": 8,
            "use":  ["maintain", "report"],
        }
    },



    "test_msgs": {
        "interval": 1000,
        "msgs": {
            "COM_UPLOAD_DEV_STATUS": 0,
            "COM_UPLOAD_RECORD.Data[0].RecordType.30001": 0,
            "COM_UPLOAD_EVENT.Data[0].EventType.NFC_EVENT": 0,
        }
    }
}


# 注册设备支持的消息
Command_list = {
    "COM_HEARTBEAT": {"msg": "心跳"},
    "COM_UPLOAD_DEV_STATUS": {"msg": "设备状态上报"},
    "COM_UPLOAD_RECORD": {"msg": "记录上传"},
    "COM_UPLOAD_EVENT": {"msg": "事件上报"},
    "COM_DEV_REGISTER": {"msg": "设备注册"},
    "COM_QUERY_DIR": {"msg": "设备目录查询"},
    "COM_DEV_RESET": {"msg": "恢复出厂设置"},
    "COM_READ_TIME": {"msg": "读取时间"},
    "COM_SET_TIME": {"msg": "设置时间"},
    "COM_CORRECTION": {"msg": "立即校时"},
    "COM_READ_SYSTEM_VERSION": {"msg": "读取系统版本信息"},
    "COM_NOTIFY_UPDATE": {"msg": "通知设备升级"},
    "COM_READ_PARAMETER": {"msg": "读取参数"},
    "COM_SETTING_PARAMETERS": {"msg": "设置参数"},
    "COM_LOAD_CERTIFICATE": {"msg": "下发固定凭证信息"},
    "COM_READ_CERTIFICATE": {"msg": "读取固定凭证信息"},
    "COM_DELETE_CERTIFICATE": {"msg": "删除固定凭证信息"},
    "COM_LOAD_CERTIFICATE_IN_BATCH": {"msg": "批量下发固定凭证信息"},
    "COM_DELETE_CERTIFICATE_IN_BATCH": {"msg": "清除固定凭证操作"},
    "COM_GATE_CONTROL": {"msg": "开关闸（门）"},
    "COM_QUERY_DEV_STATUS": {"msg": "设备状态查询"},
}


# 定制设备需要主动发的消息
u'''心跳'''
COM_HEARTBEAT = {
    "send_msg": {
        "Command": 'COM_HEARTBEAT',
    }
}


u'''事件上报：设备状态上报'''
COM_UPLOAD_DEV_STATUS = {
    "send_msg": {
        "Command": 'COM_UPLOAD_DEV_STATUS',
        "Data": [
            {
                "deciceType": "##self._type##",
                "deviceID": "##self._deviceID##",
                "deciceStatus": "##self._State##",
            }
        ]
    }
}


u'''事件上报：记录上传'''
COM_UPLOAD_RECORD = {
    "send_msg": {
        "Command": 'COM_UPLOAD_RECORD',
        "EventCode": "will_be_replace",
        "Data": [
                {
                    "deviceID": "##self._deviceID##",
                    "recordTime": "TIMENOW",
                    "RecordType": "will_be_replace",
                    "CredenceType": "##self._CredenceType##",
                    "passType": 0,
                }
        ]
    }
}

u'''事件上报：事件上报'''
COM_UPLOAD_EVENT = {
    "send_msg": {
        "Command": 'COM_UPLOAD_EVENT',
        "Data": [
                {
                    "EventType": "will_be_replace",
                    "Time": "TIMENOW",
                }
        ]
    }
}

u'''功能命令：设备注册'''
COM_DEV_REGISTER = {
    "send_msg": {
        "Command": "COM_DEV_REGISTER",
        "Data": [
            {
                "Type": "##self._type##",
                "deviceID": "##self._deviceID##",
                "manufacturer": "##self._manufacturer##",
                "ip": "##self._ip##",
                "mac": "##self._mac##",
                "mask": "##self._mask##",
                "version": "##self._version##",
            }
        ]
    }
}


# 定制设备需要应答的消息
u'''功能命令：设备目录查询'''
COM_QUERY_DIR = {
    'set_item': {},
    "rsp_msg": {
        "Command": "COM_QUERY_DIR",
        "Result": 0,
        "Data": [
            {
                "deviceID": "##self._deviceID##",
                "name": "##self._name##",
                "manufacturer": "##self._manufacturer##",
                "version": "##self._version##",
                "subDeviceType": "##self.subDeviceType##"
            }
        ]
    }
}


u'''功能命令：恢复出厂设置'''
COM_DEV_RESET = {
    'set_item': {},
    "rsp_msg": {
        "Command": "COM_DEV_RESET",
        "Result": 0,
    }
}

u'''功能命令：读取时间'''
COM_READ_TIME = {
    'set_item': {},
    "rsp_msg": {
        "Command": "COM_READ_TIME",
        "Result": 0,
        "Data": [
            {
                "time": "##self._time##"
            }
        ]
    }
}


u'''功能命令：设置时间'''
COM_SET_TIME = {
    'set_item': {'_time': 'Data.time'},
    "rsp_msg": {
        "Command": "COM_SET_TIME",
        "Result": 0,
    }
}

u'''功能命令：立即校时'''
COM_CORRECTION = {
    'set_item': {},
    "rsp_msg": {
        "Command": "COM_CORRECTION",
        "Result": 0,
    }

}


u'''功能命令：读取系统版本信息'''
COM_READ_SYSTEM_VERSION = {
    'set_item': {},
    "rsp_msg": {
        "Command": "COM_READ_SYSTEM_VERSION",
        "Result": 0,
        "Data": [
            {
                "appVersionInfo": "##self._appVersionInfo##"
            }
        ]
    }

}


u'''功能命令：通知设备升级'''
COM_NOTIFY_UPDATE = {
    'set_item': {'_version': 'Data.newVersion'},
    "rsp_msg": {
        "Command": "COM_NOTIFY_UPDATE",
        "Result": 0,
        "Data": [
               {
                   "appVersionInfo": "##self._appVersionInfo##"
               }
        ]
    }

}


u'''功能命令：读取参数'''
COM_READ_PARAMETER = {
    'set_item': {},
    "rsp_msg": {
        "Command": "COM_READ_PARAMETER",
        "Result": 0,
        "Data": [
            {
                "deviceID": "##self._deviceID##",
                "fileServerUrl": "##self._fileServerUrl##",
                "ntpServer": "##self._ntpServer##",
                "openDuration": "##self._openDuration##",
                "alarmTimeout": "##self._alarmTimeout##",
            }
        ]
    }

}


u'''功能命令：设置参数'''
COM_SETTING_PARAMETERS = {
    "set_item": {"_fileServerUrl": "Data.fileServerUrl", "_ntpServer": "Data.ntpServer", "_alarmTimeout": "Data.alarmTimeout", "_openDuration": "Data.openDuration"},
    "rsp_msg": {
        "Command": "COM_SETTING_PARAMETERS",
        "Result": 0,
    }
}


u'''功能命令：下发固定凭证信息'''
COM_LOAD_CERTIFICATE = {
    "set_item": {"_startTime": "Data.startTime", "_endTime": "Data.endTime", "_subDeviceID": "Data.subDeviceID",
                 "_UserType": "Data.UserType", "_CredenceType": "Data.CredenceType", "_credenceNo": "Data.credenceNo", },
    "rsp_msg": {
        "Command": "COM_LOAD_CERTIFICATE",
        "Result": 0,
    }
}

u'''功能命令：读取固定凭证信息'''
COM_READ_CERTIFICATE = {
    'set_item': {},
    "rsp_msg": {
        "Command": "COM_READ_CERTIFICATE",
        "Result": 0,
        "Data": [
            {
                "startTime": "##self._startTime##",
                "endTime": "##self._endTime##",
                "CredenceType": "##self._CredenceType##",
                "credenceNo": "##self._credenceNo##",
            }
        ]
    }
}


u'''功能命令：删除固定凭证信息'''
COM_DELETE_CERTIFICATE = {
    'set_item': {},
    "rsp_msg": {
        "Command": "COM_DELETE_CERTIFICATE",
        "Result": 0,
    }
}

u'''功能命令：批量下发固定凭证信息'''
COM_LOAD_CERTIFICATE_IN_BATCH = {
    'set_item': {},
    "rsp_msg": {
        "Command": "COM_LOAD_CERTIFICATE_IN_BATCH",
        "Result": 0,
    }
}

u'''功能命令：开关闸（门）'''
COM_GATE_CONTROL = {
    "set_item": {"_State": "Data.operateType", "_userID": "Data.userID", "_userType": "Data.userType"},
    "rsp_msg": {
        "Command": "COM_GATE_CONTROL",
        "Result": 0,
    }
}

u'''功能命令：设备状态查询'''
COM_QUERY_DEV_STATUS = {
    'set_item': {},
    "rsp_msg": {
        "Command": "COM_QUERY_DEV_STATUS",
        "Result": 0,
        "Data": [
            {
                "State": "##self._State##",
            }
        ]
    }
}
