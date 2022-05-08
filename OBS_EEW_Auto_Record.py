import obspython
import time
import urllib.request
import urllib.parse
import json

source_name = ""
source_name2 = ""
interval = 1
ptime = 0
eew = 0
enabled = False
test = False

def script_load(setting):
    global timeArray
    obspython.script_log(obspython.LOG_INFO, "脚本载入成功")
    latest = urllib.request.urlopen("http://www.kmoni.bosai.go.jp/webservice/server/pros/latest.json")
    a = latest.read()
    timeArray = time.strptime(str(a)[129:148], "%Y/%m/%d %H:%M:%S")
    obspython.script_log(obspython.LOG_INFO, str(timeArray))


def script_description():
    return """
        通过NIED的API进行EEW判断
        文字源用来显示插件状态和EEW发表状态
        
        
        特别鸣谢：鸣谢了个寂寞
        """


def script_properties():
    pros = obspython.obs_properties_create()
    obspython.obs_properties_add_bool(pros, "enabled", "启用")
    obspython.obs_properties_add_bool(pros, "test", "测试-默认关闭")
    obspython.obs_properties_add_int(pros, "interval", "更新间隔（1-60秒）", 1, 60, 1)
    text_source = obspython.obs_properties_add_list(pros, "source_name", "文字源", obspython.OBS_COMBO_TYPE_LIST,obspython.OBS_COMBO_FORMAT_STRING)
    sources = obspython.obs_enum_sources()
    if sources:
        for source in sources:
            source_id = obspython.obs_source_get_unversioned_id(source)
            if source_id in ("text_gdiplus", "text_ft2_source"):
                name = obspython.obs_source_get_name(source)
                obspython.obs_property_list_add_string(text_source, name, name)
        obspython.source_list_release(sources)
    obspython.obs_properties_add_button(pros, "refresh", "立即刷新数据", refresh_pressed)
    return pros


def refresh_pressed(pros, prop):
    global timeArray
    global ptime
    latest = urllib.request.urlopen("http://www.kmoni.bosai.go.jp/webservice/server/pros/latest.json")
    a = latest.read()
    timeArray = time.strptime(str(a)[129:148], "%Y/%m/%d %H:%M:%S")
    ptime = 0
    update()


def script_defaults(settings):
    obspython.obs_data_set_default_int(settings, "interval", 1)


def script_update(setting):
    global inverval
    global source_name
    global enabled
    global test
    enabled = obspython.obs_data_get_bool(setting, "enabled")
    test = obspython.obs_data_get_bool(setting, "test")
    source_name = obspython.obs_data_get_string(setting, "source_name")
    interval = obspython.obs_data_get_int(setting, "interval")
    if enabled:
        obspython.timer_remove(update)
        obspython.timer_remove(timer)
        obspython.timer_add(update, interval * 1000)
        obspython.timer_add(timer, 1000)
    else:
        obspython.timer_remove(update)
        msm = "插件已关闭"
        source = obspython.obs_get_source_by_name(source_name)
        obspython.obs_data_set_string(setting, "text", f"{msm}")
        obspython.obs_source_update(source, setting)
        obspython.obs_data_release(setting)
        obspython.obs_source_release(source)


def update():
    global source_name
    global ptime
    global timeArray
    global eew
    global test

    source = obspython.obs_get_source_by_name(source_name)
    if source:
        setting = obspython.obs_data_create()
        # msm = time.strftime("%H:%M:%S", time.localtime(int(time.time()) - ptime))
        # response = urllib.request.urlopen("http://www.kmoni.bosai.go.jp/webservice/hypo/eew/"+time.strftime("%Y%m%d%H%M%S", timeArray)+".json")
        if test:
            response = urllib.request.urlopen("http://www.kmoni.bosai.go.jp/webservice/hypo/eew/20220316233503.json")
            obspython.script_log(obspython.LOG_INFO, "测试")
        else:
            timed = str(time.strftime("%Y%m%d%H%M%S", (time.localtime(int(time.mktime(timeArray)) + ptime))))
            response = urllib.request.urlopen("http://www.kmoni.bosai.go.jp/webservice/hypo/eew/" + timed + ".json")
            obspython.script_log(obspython.LOG_INFO, str(time.strftime("%Y%m%d%H%M%S", (time.localtime(int(time.mktime(timeArray)) + ptime)))))
        json_str = response.read()
        #obspython.script_log(obspython.LOG_INFO, "ptime" + str(ptime))
        data = json.loads(json_str)
        #msm = str(data["request_time"]) + str(data["result"])
        if str(data["report_id"]) == "":
            msm = "当前未发布地震信息"
            obspython.obs_data_set_string(setting, "text", f"{msm}")
            obspython.obs_source_update(source, setting)
            obspython.obs_data_release(setting)
            obspython.obs_source_release(source)
            if eew == 1:
                eew = 0
                obspython.obs_frontend_recording_stop()
                obspython.script_log(obspython.LOG_INFO, "停止录制" + str(timed))
            else:
                return 0
        else:
            msm = "EEW发表中"
            obspython.obs_data_set_string(setting, "text", f"{msm}")
            obspython.obs_source_update(source, setting)
            obspython.obs_data_release(setting)
            obspython.obs_source_release(source)
            if eew == 0:
                eew = 1
                obspython.obs_frontend_recording_start()
                obspython.obs_frontend_replay_buffer_save()
                obspython.script_log(obspython.LOG_INFO, "开始录制" + str(timed))
            else:
                return 0

def timer():
    global ptime
    #obspython.script_log(obspython.LOG_INFO, "A")
    ptime = ptime + 1
