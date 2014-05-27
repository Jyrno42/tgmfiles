from tgmfiles.views import FileUploadView

try:  # pre 1.6
    from django.conf.urls.defaults import url, patterns
except ImportError:
    from django.conf.urls import url, patterns

urlpatterns = patterns(
    '',

    # for Testing
    url('^tgm-upload/', FileUploadView.as_view(), name='tgm-file-upload'),
)
