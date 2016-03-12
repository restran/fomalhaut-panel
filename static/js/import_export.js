/**
 * created by restran on 2016/03/13.
 */

(function () {
    // 使用 vue 来做导入导出
    var app = new Vue({
        el: '#nav-bar-app',
        data: {
            has_response: false,
            response: {'success': false, 'msg': '', 'errors': []},
            processDone: false,
            processMsg: '',
            processPercentage: 0,
            processInterval: null,
            realProcessPercentage: 0
        },
        methods: {
            init: function () {
                // 是否已经有回应的数据
                this.has_response = false;
                this.response = {'success': false, 'msg': '', 'errors': []};

                // 进度条
                this.processDone = false;
                this.processMsg = '';
                this.processPercentage = 0;
                this.processInterval = null;
                this.realProcessPercentage = 0;
            },
            uploadConfig: function () {
                $('#upload-config-modal').modal('show');
                app.init();
                var progressbar = $('#upload-progress-bar');
                progressbar.addClass('hidden');
            },
            closeImportModal: function () {
                // 导入成功需要刷新页面
                if (this.response['success'] == true) {
                    document.location.href = '/dashboard/config/';
                }
            }
        },
        computed: {}
    });
    app.init();

    var uploader = new plupload.Uploader({
        runtimes: 'html5,flash,silverlight,html4',
        browse_button: 'pickfiles', // you can pass in id...
        container: document.getElementById('upload-file-container'), // ... or DOM Element itself
        url: '/api/dashboard/upload/import/',
        flash_swf_url: '/static/js/plupload/Moxie.swf',
        silverlight_xap_url: '/static/js/plupload/Moxie.xap',
        multipart_params: {"csrfmiddlewaretoken": getCookie('csrftoken')},
        multi_selection: false,
        auto_start: true,
        max_file_size: '10mb',
        unique_names: true,
        // disable chunk
        chunk_size: 0,
        //chunk_size: '10mb',
        filters: {
            max_file_size: '10mb',
            mime_types: [
                {title: "json files", extensions: "json"}
            ]
        },

        init: {
            'FilesAdded': function (up, files) {
                var progressbar = $('#upload-progress-bar');
                progressbar.removeClass('hidden');
                uploader.start();

                app.processDone = false;
                app.processMsg = '文件上传中...';
                app.processPercentage = 0;
                app.realProcessPercentage = 0;
                app.has_response = false;

                if (app.processInterval != null) {
                    clearInterval(app.processInterval);
                    app.processInterval = null;
                }

            },
            'UploadProgress': function (uploader, file) {
                console.log('UploadProgress');
                app.realProcessPercentage = Math.floor(file.percent * 10 / 100);
                app.processPercentage = app.realProcessPercentage;
                //var uploaded = file.loaded;
                //var size = plupload.formatSize(uploaded).toUpperCase();
                //
                //console.log(size);
                if (file.percent == 100) {
                    app.processMsg = '数据处理中...';
                    app.startProcess();
                }
                //setProgress(file, 'upload-progress-bar', file.percent, uploader.total.bytesPerSec);
            },
            'UploadComplete': function (uploader, files) {
                //var progressbar = $('#upload-progress-bar');
                //$('#upload-progress-bar').css('opacity', 0);
                //progressbar.addClass('hidden');
                //progressbar.find('progress-bar').attr('aria-valuenow', 0).css('width', "0%");
            },
            'FileUploaded': function (uploader, file, response) {
                //每个文件上传成功后,处理相关的事情
                //其中 info 是文件上传成功后，服务端返回数据
                app.has_response = true;
                try {
                    app.response = JSON.parse(response.response);
                } catch (err) {
                    app.response['success'] = false;
                    app.response['msg'] = '上传失败，服务器未正确响应';
                    app.response['errors'] = [];
                    app.response['success_msgs'] = [];
                }

                app.setProcessDone();
            },
            'Error': function (uploader, error) {
                app.has_response = true;
                try {
                    app.response = JSON.parse(error.response);
                } catch (err) {
                    app.response['success'] = false;
                    app.response['msg'] = '上传失败，请选择 JSON 文件';
                    app.response['errors'] = [];
                    app.response['success_msgs'] = [];
                }

                app.setProcessDone();

            }
        }
    });

    uploader.init();

    // 文件上传完成后，开始显示处理Excel的进度信息
    app.startProcess = function () {
        if (app.processInterval == null) {
            app.processInterval = setInterval(function () {
                if (app.realProcessPercentage < 50) {
                    app.realProcessPercentage += 2;
                } else if (app.realProcessPercentage < 80) {
                    app.realProcessPercentage += 1;
                } else if (app.realProcessPercentage < 90) {
                    app.realProcessPercentage += 0.5;
                } else if (app.realProcessPercentage < 95) {
                    app.realProcessPercentage += 0.1;
                } else if (app.realProcessPercentage < 99) {
                    app.realProcessPercentage += 0.01;
                } else {
                }
                app.processPercentage = Math.floor(app.realProcessPercentage);
            }, 250);
        }
    };

    app.setProcessDone = function () {
        if (app.processInterval != null) {
            clearInterval(app.processInterval);
            app.processInterval = null;
        }
        app.processPercentage = 100;
        app.processMsg = '处理完成';
    };
})();