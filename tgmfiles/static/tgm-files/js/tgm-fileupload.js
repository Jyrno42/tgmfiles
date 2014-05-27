
(function($) {
    "use strict";

    function setup($el, is_multi) {
        if (!$el.data('uploader-initialized')) {
            $el.data('uploader-initialized', true);

            var $fileInput = $el.find('input[type="file"]');

            var $removeBtn = $el.find('.close'),
                $deleteInput = null,
                upload_url = $el.data('upload-url'),
                $progressBar = $el.find('.progress-bar'),
                $imagePreview = $el.find('img'),
                $md5sum = $el.find('input[name="' + $fileInput.attr('name') + '_md5sum"]'),
                $fqField = $el.find('input[name="' + $fileInput.attr('name') + '_FQ"]');

            var toggleAddButton = function () { };

            if (is_multi) {
                var field_name = $fileInput.attr('name').replace(/(-?[\d]+-)[\w\-_]+$/, '');
                var $addBtn = $el.parents('form').find('[data-add-new="' + field_name + '"]');
                var $container = $el.parents('form').find('[data-multi-container="' + field_name + '"]');

                toggleAddButton = function () {
                    $addBtn.prop('disabled', $container.find('.file-uploader.multi-uploader')
                        .not('.has-image').length < 1);
                };

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

                console.log('remove', $deleteInput, $deleteInput.prop('checked'));

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
                    $el.parents('.controller').find('.field-error').html('');
                    $progressBar.css({width: '1%'});
                    $el.removeClass('has-image').removeClass('is-file').addClass('with-progress');

                    data.submit();
                },

                progress: function(e, data) {
                    var progress = parseInt(data.loaded / data.total * 100, 10);
                    $progressBar.css({width: progress + '%'});
                },

                error: function(e, data) {
                    $el.removeClass('has-image').removeClass('is-file').removeClass('with-progress');

                    var resp = e.responseJSON;
                    if (resp && resp.errors) {
                        var $errElem = $el.parents('.controller').find('.field-error');
                        if ($errElem.length === 0) {
                            $el.parents('.controller').append($('div').addClass('field-error'));
                            $errElem = $el.parents('.controller').find('.field-error');
                        }
                        $errElem.html(resp.errors)
                    } else {
                        alert('Oops, file upload failed, please try again');
                    }
                    toggleAddButton();
                },

                done: function(e, data) {
                    if (data.result && data.result.success) {
                        $el.parents('.controller').find('.field-error').html('');

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

    $(document).ready(function () {
        $('.file-uploader.single-uploader').each(function(i, el) {
            setup($(el));
        });
        $('.file-uploader.multi-uploader').each(function(i, el) {
            setup($(el), true);
        });
    });

})(window.jQuery);
