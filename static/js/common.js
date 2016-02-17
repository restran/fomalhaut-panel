/**
 * Created by restran on 2015/5/12.
 */

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

