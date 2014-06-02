
(function($) {
    "use strict";



    function setProgress($bar, reversed, amount) {
        if (reversed) {
            amount = 1 - amount;
        }

        var progress = parseInt(amount * 100, 10);
        $bar.css({width: progress + '%'});
    }

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
                $controls = $el.parents('.controls'),
                $dropContainer = $el,
                reversed = $progressBar.data('reverse') || false;

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
            var getNextFileInput = function ($startFrom, idx) {
                return $el;
            };

            if (is_multi) {
                var field_name = $fileInput.attr('name').replace(/(-?[\d]+-)[\w\-_]+$/, '');
                var $addBtn = $el.parents('form').find('[data-add-new="' + field_name + '"]');
                $dropContainer = $el.parents('form').find('[data-drop-area="' + field_name + '"]');
                var $container = $el.parents('form').find('[data-multi-container="' + field_name + '"]');

                toggleAddButton = function () {
                    $addBtn.prop('disabled', $container.find('.file-uploader.multi-uploader')
                        .not('.has-image').length < 1);
                };

                $controls = $addBtn.parent();

                getNextFileInput = function ($startFrom, idx) {
                    var pre_add_cb = $addBtn.data('pre-add-cb');
                    var the_item = null;

                    if (typeof pre_add_cb === 'function') {
                        // TODO: Js class so this gets a lot easier. (can be hooked into with different events)
                        the_item = pre_add_cb.call(
                            $addBtn,
                            $container,
                            setup
                        );
                    }

                    if (!the_item || the_item.length === 0) {
                        var $selector = $container.find('.file-uploader.multi-uploader').not('.has-image');

                        if ($startFrom && $startFrom.length > 0) {
                            if (idx === 0) {
                                the_item = $startFrom;
                            } else {
                                the_item = $selector.eq($startFrom.index() + idx);
                            }
                        } else {
                            the_item = $selector.first();
                        }
                    }

                    return the_item;
                };

                if (!$addBtn.data('uploader-initialized')) {
                    $addBtn.data('uploader-initialized', true);

                    var pre_add_cb = $addBtn.data('pre-add-cb');

                    $addBtn.on('click.data-add-' + field_name, function (e) {
                        e.preventDefault();
                        toggleAddButton();

                        getNextFileInput().find('input[type=file]').trigger('click');
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

            var maskCss = {
                'position': 'absolute',
                'left': '-' + $dropContainer.css('border-left-width'),
                'right': '-' + $dropContainer.css('border-right-width'),
                'top': '-' + $dropContainer.css('border-top-width'),
                'bottom': '-' + $dropContainer.css('border-bottom-width')
            };
            $dropContainer.append($('<div class="drop-mask"></div>').css(maskCss));

            $dropContainer.find('.drop-mask').off('dragover dragleave dragend drop');

            $dropContainer.on('dragover', function () {
                $dropContainer.addClass('drag-active');
            });

            $dropContainer.find('.drop-mask').on('dragleave dragend', function () {
                $dropContainer.removeClass('drag-active');
            });
            $dropContainer.find('.drop-mask').on('drop', function (e) {
                e.preventDefault();

                $dropContainer.removeClass('drag-active');

                var dataTransfer = e.dataTransfer = e.originalEvent.dataTransfer;

                if (dataTransfer.files.length <= 1) {
                    getNextFileInput().find('input[type=file]').data( "blueimp-fileupload")._onDrop(e);
                } else {
                    var $next = getNextFileInput();
                    var fileWidgetObj = $next.find('input[type=file]').data( "blueimp-fileupload");

                    fileWidgetObj._getDroppedFiles(dataTransfer).always(function (files) {
                        for (var i = 0; i < files.length; i += 1) {
                            var data = {
                                files: [files[i]]
                            };
                            var clEvent = new window.Event('drop');

                            var $nowObj = getNextFileInput($next, i).find('input[type=file]').data( "blueimp-fileupload");
                            if ($nowObj._trigger('drop', clEvent, data) !== false) {
                                $nowObj._onAdd(clEvent, data);
                            }
                        }
                    });
                }

                toggleAddButton();
            });

            $fileInput.fileupload({
                url: upload_url,
                dataType: 'json',
                paramName: 'file',
                dropZone: $el,

                formData: {
                    'fq': $fqField.val()
                },

                add: function(e, data) {
                    var is_image = false;
                    if (data.files.length > 0) {
                        is_image = data.files[0].type.match(/image./) || false;
                    }

                    $el.toggleClass('is-file', !is_image);
                    $el.addClass('with-preview');

                    $controls.find('.upload-field-error').html('');

                    // If FileReader api is available we can add images before upload.
                    if (is_image && window.FileReader) {
                        var reader  = new FileReader();

                        reader.onloadend = function () {
                            $el.addClass('with-preview');
                            $imagePreview.attr('src', reader.result);
                        };

                        reader.readAsDataURL(data.files[0]);
                    }

                    if(data.originalFiles[0].size && data.originalFiles[0].size > parseInt(max_size, 10)) {
                        addError($el.data('size-error'));
                    } else {
                        setProgress($progressBar, reversed, 0.01);
                        $el.removeClass('has-image').addClass('with-progress');
                        data.submit();
                    }
                },

                progress: function(e, data) {
                    setProgress($progressBar, reversed, data.loaded / data.total);
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
                        setProgress($progressBar, reversed, 1);
                        $controls.find('.upload-field-error').html('');
                        $controls.addClass('has-error');

                        $el.removeClass('with-preview').removeClass('with-progress').addClass('has-image');
                        $md5sum.val(data.result.file.md5sum);
                        $deleteInput.prop('checked', false);

                        $el.toggleClass('is-file', data.result.file.instance_type === 'file');

                        if (data.result.file.instance_type === 'image') {
                            $imagePreview.attr('src', data.result.file.url);
                        }

                        var nameParts = data.result.file.file_name.split('/');
                        $el.find('[data-file-name]').text(nameParts[nameParts.length - 1]);

                        $dropContainer.trigger('tgm_file_changed', [$el, $fileInput, nameParts[nameParts.length - 1]]);

                        toggleAddButton();
                    }
                }
            });
        }
    }

    $(document).ready(function () {
        $('.file-uploader').each(function(i, el) {
            setup($(el), $(el).hasClass('multi-uploader'));
        });

        $(document).bind('drop dragover', function (e) {
            e.preventDefault();
        });

        $(document).bind('drop', function (e) {
            e.preventDefault();
            e.stopPropagation();

            $('.drag-active').removeClass('drag-active');
        });
    });

})(window.jQuery);
