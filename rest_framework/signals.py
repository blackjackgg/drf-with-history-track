# -*- coding: utf-8 -*-
# 创建信号
import datetime

import dictdiffer
from django.dispatch import Signal
from django.apps import apps as django_apps
import json


def format_value(value):
    """格式化数据"""
    if isinstance(value, datetime.datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return value


def show_change(olddict, newdict):
    """比较两个字典 返回如  [{'field': 'data.sex', 'old': '\xe7\x94\xb7', 'new': '\xe5\xa5\xb3'}, {'field': 'template', 'old': '', 'new': '11'}] """
    changelist = []
    listchangedict = {}
    from dictdiffer.utils import dot_lookup

    for diff in list(dictdiffer.diff(olddict, newdict)):
        changedict = {}
        diff = list(diff)
        # print("Rawdifff", diff)

        # print(diff,"difffffffffffffff")
        if diff[0] == "change":
            # 这里重新格式化一下
            changedict["field"] = diff[1]
            changedict["old"] = format_value(diff[2][0])
            changedict["new"] = format_value(diff[2][1])
            changelist.append(changedict)
            try:
                if isinstance(diff[1], list):
                    changename = ".".join(diff[1][0:-1])
                    listchangedict[changename] = {"old": dot_lookup(olddict, changename),
                                                  "new": dot_lookup(newdict, changename)}
            except Exception as e:
                print(e)

        if diff[0] == "remove" or diff[0] == "add":
            changename = diff[1]
            listchangedict[changename] = {"old": dot_lookup(olddict, changename),
                                          "new": dot_lookup(newdict, changename)}

    for key, value in listchangedict.items():
        tmpdict = {"field": key, "old": value["old"], "new": value["new"]}
        if isinstance(value["new"], list) and isinstance(value["old"], list):
            if value["new"] and (isinstance(value["new"][0], dict) or isinstance(value["new"][0], list)):  # 排除掉字典类的
                continue
            if value["old"] and (isinstance(value["old"][0], dict) or isinstance(value["old"][0], list)):  # 排除掉字典类的
                continue
            changelist.append(tmpdict)

    # print("changelist", changelist)
    return changelist


api_created = Signal()

api_updated = Signal(providing_args=["old_data", "new_data", ])


def save_history(instance, user, action="--", field_name="--"):
    """保存到数据库"""
    HISmodel = django_apps.get_model(app_label='track_actions', model_name="History", require_ready=False)
    if HISmodel:
        try:
            history = HISmodel(
                table_name=str(instance._meta.db_table),
                user=user,
                instance_id=instance.id,
                action=action,
                field_name=field_name
            )
            history.save()
        except ValueError as e:
            print(e)
        except Exception as e:
            print(e)


def created(sender, **kwargs):
    print("create")
    print(sender, kwargs)


def formate_bool(change):  # 格式化日志布尔类型为中文显示
    bool_list = {True: "是", False: "否"}
    new_data = bool_list.get(change.get("new"), change.get("new"))
    old_data = bool_list.get(change.get("old"), change.get("old"))
    change.update(**{"new": new_data, "old": old_data})
    return change


def formate_chioce(option, change):  # 格式choice类型函数
    new_data = option.get(change.get("new"), change.get("new"))
    old_data = option.get(change.get("old"), change.get("old"))
    change.update(**{"new": new_data, "old": old_data})
    return change


def formate_mutichioce(option, change):  # 格式化多选类型函数

    new_data = []
    old_data = []

    for ii in option:
        if ii['id'] in change.get("new", []):
            new_data.append(ii['name'])
        if ii['id'] in change.get("old", []):
            old_data.append(ii['name'])

    change.update(**{"new": ",".join(new_data), "old": ",".join(old_data)})

    return change


def loop_zh_name(ser, field_name, change={}):
    """循环ser获得中文名  选项名  键的类型"""
    from django.db.models import ManyToManyField, NullBooleanField, BooleanField
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
                # res = [True, zh_name, ser1, field_name1]

                # 根据不同的类型 格式化一下返回体
                field = ser1.Meta.model._meta.get_field(field_name1)
                if hasattr(field, "choices") and field.choices != []:  # 格式化单选
                    option = dict(field.choices)
                    change = formate_chioce(option, change)

                elif isinstance(field, (NullBooleanField, BooleanField)):
                    change = formate_bool(change)

                elif isinstance(field, (ManyToManyField,)):  # 格式化多选
                    BaseMultiChoices = django_apps.get_model(app_label='chestpain', model_name="BaseMultiChoices",
                                                             require_ready=False)
                    option = BaseMultiChoices.objects.filter(choices_type=field.name).values("id", "name")

                    change = formate_mutichioce(option, change)

                change.update(field=zh_name)

                res = [True, zh_name, change]

            return res
        else:
            zh_name = ser.Meta.model._meta.get_field(field_name).verbose_name
            return [True, zh_name, change]
    except Exception as e:
        print("error2", e)  # 出错这个内容不保存
        return [True, field_name, {}]


def get_zh_name(ser, field_name, change={}):
    while True:
        res = loop_zh_name(ser, field_name, change)
        is_end = res[0]

        if is_end:
            return res[2]
            break
        else:
            ser = res[2]
            field_name = res[3]


def map_nullfalse(str):
    if str in ["null", "", "Null", "NULL", "None", "none", None]:
        return "未填写"
    return str


def updated(sender, **kwargs):
    old_data = kwargs.get("old_data")
    new_data = kwargs.get("new_data")
    instance = kwargs.get("instance")
    current_request = kwargs.get("current_request")
    change = show_change(old_data, new_data)

    # sender 是序列化器 尝试通过serializer获取fieldname 没有的话就用英文名
    # print("changelist", change)

    wronglist = []
    for index, item in enumerate(change):
        field_name = item['field']
        # 这里有嵌套结构 嵌套接口单独分析
        new_item = get_zh_name(sender, field_name, item)
        item.update(**new_item)
        if not new_item:
            wronglist.append(index)

    for num, i in enumerate(wronglist):
        change.pop(i - num)

    # 获取中文名
    # print("change-----",change)

    # 获取单选项

    # 获取多选项

    # change = reform_change(change)
    try:
        # 如果建了历史记录的表 就进行记录的操作
        if change:
            for i in change:
                # print("field", i["field"], isinstance(i["field"], list), type(i["field"]))
                if "last_modified" in i["field"] or u"最近更新时间" in i["field"] or isinstance(i["field"],
                                                                                          list) or u"创建时间" in i[
                    "field"] or (not i['old'] and not i["new"]) or i['old'] == i['new'] or "id" in i["field"] or "ID" in \
                        i["field"]:
                    continue

                changestr = u"由%s更新为%s" % (str(map_nullfalse(i["old"])), str(map_nullfalse(i["new"])))

                save_history(instance, user=current_request.user, action=changestr, field_name=i["field"])
    except Exception as e:
        print(e)


api_created.connect(created)  # 注册信号
api_updated.connect(updated)  # 注册信号
