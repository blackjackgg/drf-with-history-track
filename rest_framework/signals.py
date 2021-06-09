# -*- coding: utf-8 -*-
# 创建信号
import datetime

import dictdiffer
from django.dispatch import Signal
from django.apps import apps as django_apps
import json
from track_actions.requestMiddleware import RequestMiddleware


def format_value(value):
    """格式化数据"""
    if isinstance(value, datetime.datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return value


def show_change(olddict, newdict):
    """比较两个字典 返回如  [{'field': 'data.sex', 'old': '\xe7\x94\xb7', 'new': '\xe5\xa5\xb3'}, {'field': 'template', 'old': '', 'new': '11'}] """
    changelist = []

    for diff in list(dictdiffer.diff(olddict, newdict)):
        changedict = {}
        diff = list(diff)

        # print(diff,"difffffffffffffff")
        if diff[0] == "change":
            changedict["field"] = diff[1]
            changedict["old"] = format_value(diff[2][0])
            changedict["new"] = format_value(diff[2][1])
            changelist.append(changedict)
    return changelist


api_created = Signal()

api_updated = Signal(providing_args=["old_data", "new_data", ])


def save_history(instance, action="--", field_name="--"):
    """保存到数据库"""
    HISmodel = django_apps.get_model(app_label='track_actions', model_name="History", require_ready=False)
    if HISmodel:
        current_request = RequestMiddleware.get_request_data()[1]
        try:
            history = HISmodel(
                table_name=str(instance._meta.db_table),
                user=current_request.user,
                instance_id=instance.id,
                action=action,
                field_name=field_name
            )
            history.save()
        except ValueError:
            pass


def created(sender, **kwargs):
    print("create")
    print(sender, kwargs)


def loop_zh_name(ser, field_name):
    """循环ser获得中文名"""

    # print("ser222",ser)
    try:
        if "." in field_name:  # 这里只支持两层嵌套  不断循环
            all_list = field_name.split('.')
            model1_str = all_list[0]
            field_name1 = all_list[1::]  # 这里fieldname 应该是从头到 尾部
            field_name1 = len(field_name) > 1 and ".".join(field_name1) or field_name1[0]
            ser1 = ser.__dict__["_fields"].get(model1_str)  # 这里获取的不对

            # 根据fieldname 判断还有没下一层  没有的话直接提取 有的话进入下一个循环
            if "." in field_name1:
                res = [False, field_name1, ser1, field_name1]
            else:
                zh_name = ser1.Meta.model._meta.get_field(field_name1).verbose_name
                zh_name = u"%s-%s" % (ser1.Meta.model._meta.verbose_name, zh_name)
                res = [True, zh_name, ser1, field_name1]

            return res
        else:
            zh_name = ser.Meta.model._meta.get_field(field_name).verbose_name
            return [True, zh_name]
    except Exception as e:
        print("error2", e)
        return [True, field_name]


def get_zh_name(ser, field_name):
    while True:
        res = loop_zh_name(ser, field_name)
        is_end = res[0]

        if is_end:
            return res[1]
            break
        else:
            ser = res[2]
            field_name = res[3]


def updated(sender, **kwargs):
    print("update")
    # print(sender, kwargs)

    old_data = kwargs.get("old_data")
    new_data = kwargs.get("new_data")
    instance = kwargs.get("instance")
    change = show_change(old_data, new_data)

    # sender 是序列化器 尝试通过serializer获取fieldname 没有的话就用英文名
    print("changelist", change)

    for item in change:
        field_name = item['field']
        # 这里有嵌套结构 嵌套接口单独分析
        zh_name = get_zh_name(sender, field_name)
        item['field'] = zh_name
    # 获取中文名
    # print("change-----",change)

    # change = reform_change(change)
    try:
        # 如果建了历史记录的表 就进行记录的操作
        if change:
            for i in change:
                print("field", i["field"], isinstance(i["field"], list), type(i["field"]))

                if "last_modified" in i["field"] or u"最近更新时间" in i["field"] or isinstance(i["field"], list) or   u"创建时间" in i["field"]  or (not i['old']  and not i["new"]):
                    continue

                changestr = u"由%s更新为%s" % (str(i["old"]), str(i["new"]))
                save_history(instance, action=changestr, field_name=i["field"])
    except Exception as e:
        print(e)


api_created.connect(created)  # 注册信号
api_updated.connect(updated)  # 注册信号
