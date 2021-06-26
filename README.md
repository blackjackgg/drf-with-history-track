# [DRF with api history track][docs]

[![Build Status](https://travis-ci.org/kenneth051/drf-history.svg?branch=develop)](https://travis-ci.org/kenneth051/drf-history)  [![Coverage Status](https://coveralls.io/repos/github/kenneth051/django-track-actions/badge.svg?branch=develop)](https://coveralls.io/github/kenneth051/django-track-actions?branch=develop)  [![Maintainability](https://api.codeclimate.com/v1/badges/fc8a5a15c480d2ad117d/maintainability)](https://codeclimate.com/github/kenneth051/django-track-actions/maintainability) [![Downloads](https://pepy.tech/badge/drf-safe-jack)](https://pepy.tech/project/drf-safe-jack)[![Downloads](https://pepy.tech/badge/drf-safe-jack/month)](https://pepy.tech/project/drf-safe-jack)[![Downloads](https://pepy.tech/badge/drf-safe-jack/week)](https://pepy.tech/project/drf-history/week) [![PyPI version](https://badge.fury.io/py/drf-safe-jack.svg)](https://badge.fury.io/py/drf-safe-jack)

---

# 修改说明

此包会覆盖drf的rest_frame的包下的内容   drf基础库版本为3.9.2

主要修改为增加了signal.py 和修改了mixin的update方法 和引入了track_action的历史记录model

# 安装

```shell
pip install drf-safe-jack
```



# ADD   增加了通过post方法请求put、patch、delete方法

使用方式：在请求头header加入method 写入对应方法put或者patch等即可用post方法访问put等接口  

```python
method=put 
```

---

# ADD  增加了自动记录api接口请求历史

历史记录基于api设计而非基于model，使用simple-history等包会引入大量的历史记录表，对数据库整体结构不是很友好，

所以自己实现了一个，所有的内容保存到history这个model中,采用多线程不影响正常接口的访问速度

### 特性：

> 1.多线程保存

> 2.单个历史表 ，可根据api对应序列化器serializer内的model名来搜索历史记录

>3.中文支持 自动转换none，单选choice，多选为中文名显示

使用方式：

```python
      #  settins.py
     INSTALLED_APPS = [
         ...,
         'track_actions',
     ]

     MIDDLEWARE = [
         ... ,
         'track_actions.requestMiddleware.RequestMiddleware',
     ]
    python manage.py migrate track_actions

    # url.py
     url(u'^api/', include('track_actions.urls')), # 这个路由可自定义

    # 即可在 api/history 目录下获取到所有的历史记录
```



# 记录返回内容

```python
   # 字段预览 
            "table_name": "basic_basicrescue",  # 每个 api 里面对应的表名
            "created_at": "2021-06-26T14:29:04.838753", # 操作日期
            "instance_id": "424",   #实例id
            "action": "由未填写更新为是",  # 操作内容
            "field_name": "病人-发病时间",   # 中文的字段名
            "user": 62   # 操作用户id
            "user_obj": {  # 操作用户详情
                "id": 62,
                "username": "test_006",
                "first_name": "王五",  #
                "department": 
             }
```

# 查找某个api对应的历史记录方法

```python
/api/history/?table_name=basic_basicrescue&instance_id=412  # tablename 为表名  instance_id为对应表的实例id
```

