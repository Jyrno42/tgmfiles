
(function($) {
    "use strict";

    function setup($el, is_multi) {
        if (!$el.data('uploader-initialized')) {
            $el.data('uploader-initialized', true);

            var max_size = $el.data('max-size');
            var $fileInput = $el.find('input[type="file"]');

            var $removeBtn = $el.find('.close'),
                $deleteInput = null,
                upload_url = $el.data('upload-url'),
                $progressBar = $el.find('.progress-bar'),
                $imagePreview = $el.find('img'),
                $md5sum = $el.find('input[name="' + $fileInput.attr('name') + '_md5sum"]'),
                $fqField = $el.find('input[name="' + $fileInput.attr('name') + '_FQ"]'),
                $controls = $el.parents('.controls');

            var toggleAddButton = function () { };
            var addError = function (error) {
                var $errElem = $controls.find('.upload-field-error');
                $controls.addClass('has-error');

                if ($errElem.length === 0) {
                    $controls.append($('<div></div>')
                        .addClass('upload-field-error help-block').html(error));
                } else {
                    $errElem.html(error);
                }
            };

            if (is_multi) {
                var field_name = $fileInput.attr('name').replace(/(-?[\d]+-)[\w\-_]+$/, '');
                var $addBtn = $el.parents('form').find('[data-add-new="' + field_name + '"]');
                var $container = $el.parents('form').find('[data-multi-container="' + field_name + '"]');

                toggleAddButton = function () {
                    $addBtn.prop('disabled', $container.find('.file-uploader.multi-uploader')
                        .not('.has-image').length < 1);
                };

                $controls = $addBtn.parent();

                if (!$addBtn.data('uploader-initialized')) {
                    $addBtn.data('uploader-initialized', true);

                    $addBtn.on('click.data-add-' + field_name, function (e) {
                        e.preventDefault();
                        toggleAddButton();

                        $container.find('.file-uploader.multi-uploader').each(function () {
                            if (!$(this).hasClass('has-image')) {
                                $(this).find('input[type="file"]').trigger('click');
                                return false;
                            }
                            return true;
                        });

                        return false;
                    });
                }
                $deleteInput = $container
                    .find('input[name="' + $fileInput.attr('name').replace(/\-?[^\-]+$/, '-DELETE') + '"]');
            } else {
                $deleteInput = $el.find('input[name="' + $fileInput.attr('name') + '-DELETE' + '"]');
            }
            toggleAddButton();

            $removeBtn.on('click', function (e) {
                e.preventDefault();
                $el.removeClass('with-progress').removeClass('has-image').removeClass('is-file');
                $deleteInput.prop('checked', true);
                $md5sum.val('');
                toggleAddButton();

                return false;
            });

            $fileInput.fileupload({
                url: upload_url,
                dataType: 'json',
                paramName: 'file',

                formData: {
                    'fq': $fqField.val()
                },

                add: function(e, data) {
                    $controls.find('.upload-field-error').html('');

                    if(data.originalFiles[0].size && data.originalFiles[0].size > parseInt(max_size, 10)) {
                        addError($el.data('size-error'));
                    } else {
                        $progressBar.css({width: '1%'});
                        $el.removeClass('has-image').removeClass('is-file').addClass('with-progress');
                        data.submit();
                    }

                },

                progress: function(e, data) {
                    var progress = parseInt(data.loaded / data.total * 100, 10);
                    $progressBar.css({width: progress + '%'});
                },

                error: function(e, data) {
                    $el.removeClass('has-image').removeClass('is-file').removeClass('with-progress');

                    var resp = e.responseJSON;
                    if (resp && resp.errors) {
                        addError(resp.errors);
                    } else {
                        addError('Oops, file upload failed, please try again');
                    }
                    toggleAddButton();
                },

                done: function(e, data) {
                    if (data.result && data.result.success) {
                        $controls.find('.upload-field-error').html('');
                        $controls.addClass('has-error');

                        $el.removeClass('with-progress').addClass('has-image');
                        $md5sum.val(data.result.file.md5sum);
                        $deleteInput.prop('checked', false);

                        $el.toggleClass('is-file', data.result.file.instance_type === 'file');

                        if (data.result.file.instance_type === 'image') {
                            $imagePreview.attr('src', data.result.file.url);
                        }

                        var nameParts = data.result.file.file_name.split('/');
                        $el.find('.file-display span').text(nameParts[nameParts.length - 1]);

                        toggleAddButton();
                    }
                }
            });
        }
    }

    function setupDragDrop() {
        var $targets = $('.tgm-drag-target');

        $(document).off('dragenter.tgm-files').off('dragover.tgm-files').off('drop.tgm-files');
        $targets.off('dragenter.tgm-files').off('dragover.tgm-files').off('drop.tgm-files');

        $targets.on('dragenter.tgm-files', function (e) {
            e.stopPropagation();
            e.preventDefault();
            $(this).css('border', '2px solid #0B85A1');
        }).on('dragover.tgm-files', function (e) {
            e.stopPropagation();
            e.preventDefault();
        }).on('drop.tgm-files', function (e) {
            $(this).css('border', '2px dotted #0B85A1');
            e.preventDefault();
            var files = e.originalEvent.dataTransfer.files;
            console.log('files');
             
            //We need to send dropped files to Server
            // handleFileUpload(files,obj);
        });

        $(document).on('dragenter.tgm-files', function (e) {
            e.stopPropagation();
            e.preventDefault();
        });

        $(document).on('dragover.tgm-files', function (e) {
            e.stopPropagation();
            e.preventDefault();

            $targets.css('border', '2px dotted #0B85A1');
        });

        $(document).on('drop.tgm-files', function (e) {
            e.stopPropagation();
            e.preventDefault();
        });
    }

    $(document).ready(function () {
        $('.file-uploader.single-uploader').each(function(i, el) {
            setup($(el));
        });
        $('.file-uploader.multi-uploader').each(function(i, el) {
            setup($(el), true);
        });

        setupDragDrop();
    });

})(window.jQuery);
