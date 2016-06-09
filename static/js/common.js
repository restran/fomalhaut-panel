/**
 * Created by restran on 2015/5/12.
 */

// https://github.com/dankogai/js-base64
(function (global) {
    'use strict';
    // existing version for noConflict()
    var _Base64 = global.Base64;
    var version = "2.1.9";
    // if node.js, we use Buffer
    var buffer;
    if (typeof module !== 'undefined' && module.exports) {
        try {
            buffer = require('buffer').Buffer;
        } catch (err) {
        }
    }
    // constants
    var b64chars
        = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
    var b64tab = function (bin) {
        var t = {};
        for (var i = 0, l = bin.length; i < l; i++) t[bin.charAt(i)] = i;
        return t;
    }(b64chars);
    var fromCharCode = String.fromCharCode;
    // encoder stuff
    var cb_utob = function (c) {
        var cc;
        if (c.length < 2) {
            cc = c.charCodeAt(0);
            return cc < 0x80 ? c
                : cc < 0x800 ? (fromCharCode(0xc0 | (cc >>> 6))
            + fromCharCode(0x80 | (cc & 0x3f)))
                : (fromCharCode(0xe0 | ((cc >>> 12) & 0x0f))
            + fromCharCode(0x80 | ((cc >>> 6) & 0x3f))
            + fromCharCode(0x80 | ( cc & 0x3f)));
        } else {
            cc = 0x10000
                + (c.charCodeAt(0) - 0xD800) * 0x400
                + (c.charCodeAt(1) - 0xDC00);
            return (fromCharCode(0xf0 | ((cc >>> 18) & 0x07))
            + fromCharCode(0x80 | ((cc >>> 12) & 0x3f))
            + fromCharCode(0x80 | ((cc >>> 6) & 0x3f))
            + fromCharCode(0x80 | ( cc & 0x3f)));
        }
    };
    var re_utob = /[\uD800-\uDBFF][\uDC00-\uDFFFF]|[^\x00-\x7F]/g;
    var utob = function (u) {
        return u.replace(re_utob, cb_utob);
    };
    var cb_encode = function (ccc) {
        var padlen = [0, 2, 1][ccc.length % 3],
            ord = ccc.charCodeAt(0) << 16
                | ((ccc.length > 1 ? ccc.charCodeAt(1) : 0) << 8)
                | ((ccc.length > 2 ? ccc.charCodeAt(2) : 0)),
            chars = [
                b64chars.charAt(ord >>> 18),
                b64chars.charAt((ord >>> 12) & 63),
                padlen >= 2 ? '=' : b64chars.charAt((ord >>> 6) & 63),
                padlen >= 1 ? '=' : b64chars.charAt(ord & 63)
            ];
        return chars.join('');
    };
    var btoa = global.btoa ? function (b) {
        return global.btoa(b);
    } : function (b) {
        return b.replace(/[\s\S]{1,3}/g, cb_encode);
    };
    var _encode = buffer ? function (u) {
            return (u.constructor === buffer.constructor ? u : new buffer(u))
                .toString('base64')
        }
            : function (u) {
            return btoa(utob(u))
        }
        ;
    var encode = function (u, urisafe) {
        return !urisafe
            ? _encode(String(u))
            : _encode(String(u)).replace(/[+\/]/g, function (m0) {
            return m0 == '+' ? '-' : '_';
        }).replace(/=/g, '');
    };
    var encodeURI = function (u) {
        return encode(u, true)
    };
    // decoder stuff
    var re_btou = new RegExp([
        '[\xC0-\xDF][\x80-\xBF]',
        '[\xE0-\xEF][\x80-\xBF]{2}',
        '[\xF0-\xF7][\x80-\xBF]{3}'
    ].join('|'), 'g');
    var cb_btou = function (cccc) {
        switch (cccc.length) {
            case 4:
                var cp = ((0x07 & cccc.charCodeAt(0)) << 18)
                        | ((0x3f & cccc.charCodeAt(1)) << 12)
                        | ((0x3f & cccc.charCodeAt(2)) << 6)
                        | (0x3f & cccc.charCodeAt(3)),
                    offset = cp - 0x10000;
                return (fromCharCode((offset >>> 10) + 0xD800)
                + fromCharCode((offset & 0x3FF) + 0xDC00));
            case 3:
                return fromCharCode(
                    ((0x0f & cccc.charCodeAt(0)) << 12)
                    | ((0x3f & cccc.charCodeAt(1)) << 6)
                    | (0x3f & cccc.charCodeAt(2))
                );
            default:
                return fromCharCode(
                    ((0x1f & cccc.charCodeAt(0)) << 6)
                    | (0x3f & cccc.charCodeAt(1))
                );
        }
    };
    var btou = function (b) {
        return b.replace(re_btou, cb_btou);
    };
    var cb_decode = function (cccc) {
        var len = cccc.length,
            padlen = len % 4,
            n = (len > 0 ? b64tab[cccc.charAt(0)] << 18 : 0)
                | (len > 1 ? b64tab[cccc.charAt(1)] << 12 : 0)
                | (len > 2 ? b64tab[cccc.charAt(2)] << 6 : 0)
                | (len > 3 ? b64tab[cccc.charAt(3)] : 0),
            chars = [
                fromCharCode(n >>> 16),
                fromCharCode((n >>> 8) & 0xff),
                fromCharCode(n & 0xff)
            ];
        chars.length -= [0, 0, 2, 1][padlen];
        return chars.join('');
    };
    var atob = global.atob ? function (a) {
        return global.atob(a);
    } : function (a) {
        return a.replace(/[\s\S]{1,4}/g, cb_decode);
    };
    var _decode = buffer ? function (a) {
        return (a.constructor === buffer.constructor
            ? a : new buffer(a, 'base64')).toString();
    }
        : function (a) {
        return btou(atob(a))
    };
    var decode = function (a) {
        return _decode(
            String(a).replace(/[-_]/g, function (m0) {
                return m0 == '-' ? '+' : '/'
            })
                .replace(/[^A-Za-z0-9\+\/]/g, '')
        );
    };
    var noConflict = function () {
        var Base64 = global.Base64;
        global.Base64 = _Base64;
        return Base64;
    };
    // export Base64
    global.Base64 = {
        VERSION: version,
        atob: atob,
        btoa: btoa,
        fromBase64: decode,
        toBase64: encode,
        utob: utob,
        encode: encode,
        encodeURI: encodeURI,
        btou: btou,
        decode: decode,
        noConflict: noConflict
    };
    // if ES5 is available, make Base64.extendString() available
    if (typeof Object.defineProperty === 'function') {
        var noEnum = function (v) {
            return {value: v, enumerable: false, writable: true, configurable: true};
        };
        global.Base64.extendString = function () {
            Object.defineProperty(
                String.prototype, 'fromBase64', noEnum(function () {
                    return decode(this)
                }));
            Object.defineProperty(
                String.prototype, 'toBase64', noEnum(function (urisafe) {
                    return encode(this, urisafe)
                }));
            Object.defineProperty(
                String.prototype, 'toBase64URI', noEnum(function () {
                    return encode(this, true)
                }));
        };
    }
    // that's it!
    // if (global['Meteor']) {
    //     Base64 = global.Base64; // for normal export in Meteor.js
    // }
})(window);

$.fn.serializeObject = function () {
    var o = {};
    var a = this.serializeArray();
    $.each(a, function () {
        if (o[this.name] !== undefined) {
            if (!o[this.name].push) {
                o[this.name] = [o[this.name]];
            }
            o[this.name].push(this.value || '');
        } else {
            o[this.name] = this.value || '';
        }
    });
    return o;
};

// csrf token
$.ajaxSettings = $.extend($.ajaxSettings, {
    beforeSend: function (xhr, settings) {
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie != '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = $.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            // Only send the token to relative URLs i.e. locally.
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});

var getUrlParam = function (name, default_value) {
    //构造一个含有目标参数的正则表达式对象
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)");
    // decodeURI，处理中文问题
    var url = decodeURI(window.location.search.substr(1));
    var r = url.match(reg);  //匹配目标参数
    if (r != null) return unescape(r[2]);
    return default_value; //返回参数值
};

var getCookie = function (name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = $.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};

var $request = {
    get: function (uri, data, successCallback, errorCallback) {
        $.ajax({
            type: 'GET',
            url: uri,
            // data to be added to query string:
            data: data,
            // type of data we are expecting in return:
            dataType: 'json',
            //timeout: 30000,
            context: $('body'),
            success: function (data) {
                console.log(data);
                try {
                    if (data['success'] == true) {
                        successCallback(data);
                    } else {
                        callErrorCallback(data, errorCallback);
                    }
                } catch (e) {
                    console.log(e);
                    callErrorCallback(data, errorCallback);
                }
            },
            error: function (xhr, type) {
                console.log('Ajax error!');
                callErrorCallback(null, errorCallback);
            }
        })
    },
    post: function (uri, data, successCallback, errorCallback) {
        $.ajax({
            type: 'POST',
            url: uri,
            // data to be added to query string:
            data: JSON.stringify(data),
            // type of data we are expecting in return:
            contentType: 'application/json; charset=utf-8',
            //timeout: 30000,
            context: $('body'),
            success: function (data) {
                console.log(data);
                try {
                    if (data['success'] == true) {
                        successCallback(data);
                    } else {
                        console.log('callErrorCallback');
                        callErrorCallback(data, errorCallback);
                    }
                } catch (e) {
                    console.log(e);
                    callErrorCallback(data, errorCallback);
                }
            },
            error: function (xhr, type) {
                console.log('Ajax error!');
                callErrorCallback(null, errorCallback);
            }
        })
    },
    rawPost: function (uri, data, successCallback, errorCallback) {
        $.ajax({
            type: 'POST',
            url: uri,
            // data to be added to query string:
            data: JSON.stringify(data),
            // type of data we are expecting in return:
            contentType: 'application/json; charset=utf-8',
            //timeout: 30000,
            context: $('body'),
            success: function (data) {
                successCallback(data);
            },
            error: function (xhr, type) {
                console.log('Ajax error!');
                callErrorCallback(null, errorCallback);
            }
        })
    }
};

function callErrorCallback(data, callback) {
    if (callback != null && callback != undefined) {
        if (data != null && data['msg'] != '') {
            callback(data, data['msg']);
        } else {
            callback(data, '获取数据失败');
        }
    }
}

(function () {
    // ie8 不支持 console
    if (!window.console) {
        window.console = (function () {
            var c = {};
            c.log = c.warn = c.debug = c.info = c.error = c.time = c.dir = c.profile
                = c.clear = c.exception = c.trace = c.assert = function () {
            };
            return c;
        })();
    }

    // ie8 不支持 getComputedStyle, bootstrap-select 会使用到
    if (!window.getComputedStyle) {
        window.getComputedStyle = function (el, pseudo) {
            this.el = el;
            this.getPropertyValue = function (prop) {
                var re = /(\-([a-z]){1})/g;
                if (prop == 'float') prop = 'styleFloat';
                if (re.test(prop)) {
                    prop = prop.replace(re, function () {
                        return arguments[2].toUpperCase();
                    });
                }
                return el.currentStyle[prop] ? el.currentStyle[prop] : null;
            };
            return this;
        }
    }

    // toastr 配置
    toastr.options = {
        "closeButton": true,
        "debug": false,
        "newestOnTop": false,
        "progressBar": false,
        "positionClass": "toast-top-center",
        "preventDuplicates": true,
        "onclick": null,
        "showDuration": "300",
        "hideDuration": "1000",
        "timeOut": "3000",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
    }
})();

$(document).ready(function () {
    // 修复bootstrap 使用.navbar-fixed-top，且存在滚动条的情况下，
    // 打开模态对话框，导致导航栏向右偏17px的问题*/
    var oldSSB = $.fn.modal.Constructor.prototype.setScrollbar;
    $.fn.modal.Constructor.prototype.setScrollbar = function () {
        oldSSB.apply(this);
        if (this.bodyIsOverflowing && this.scrollbarWidth) {
            $('.navbar-fixed-top, .navbar-fixed-bottom').css('padding-right', this.scrollbarWidth);
        }
    };

    var oldRSB = $.fn.modal.Constructor.prototype.resetScrollbar;
    $.fn.modal.Constructor.prototype.resetScrollbar = function () {
        oldRSB.apply(this);
        $('.navbar-fixed-top, .navbar-fixed-bottom').css('padding-right', '');
    };


    // 回到顶部
    $(window).scroll(function () {
        //console.log($(window).scrollTop());
        //console.log($(window).height());
        //当滚动条的位置处于距顶部指定像素以下时，回到顶部按钮出现，否则消失
        if ($(window).scrollTop() > ($(window).height() / 2)) {
            $("#back-to-top").removeClass('hidden');
            //$("#back-to-top").fadeIn(1000);
        } else {
            $("#back-to-top").addClass('hidden');
            //$("#back-to-top").fadeOut(1000)
        }
    });

    $("#back-to-top").on('click', function (e) {
        $('html, body').animate({
            scrollTop: 0
        }, 1000);

    });

    //$('form').validator().on('submit', function (e) {
    //    if (e.isDefaultPrevented()) {
    //        // handle the invalid form...
    //    } else {
    //        // everything looks good!
    //    }
    //});

    try {
        $('form').validator({
            errors: {
                required: "这是必填项",
                match: "内容不匹配",
                minlength: "输入内容过少",
                maxlength: "输入内容过多"
            }
        });
    } catch (e) {

    }

});