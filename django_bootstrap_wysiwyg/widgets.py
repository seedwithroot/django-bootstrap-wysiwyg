import string
import random
from django.forms import Widget,Select
from django.template import loader
from .utils import setting
from django.forms.util import flatatt
from django.utils.encoding import force_unicode
from itertools import chain
from django.utils.html import escape, conditional_escape
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


class WysiwygInput(Widget):
    template_name = 'django_bootstrap_wysiwyg/input.html'

    # default css class of the editor element
    css_class = setting(
        "WYSIWYG_DEFAULT_CSS_CLASS",
        "editor"
    )

    # default toolbar items can be overridden via the constructor parameter
    toolbar_items = setting(
        "WYSIWYH_DEFAULT_TOOLBAR_ITEMS",
        ['fonts', 'font_size', 'font_weights', 'lists',
         'alignments', 'hyperlink', 'image', 'history', 'speech']
    )

    def __init__(self, attrs=None, toolbar_items=None):
        if toolbar_items:
            self.toolbar_items = toolbar_items
        return super(WysiwygInput, self).__init__(attrs)

    def get_context(self, name, value, attrs=None):
        context = {}
        context['attrs'] = self.build_attrs(attrs)
        context['name'] = name
        context['value'] = value
        context['toolbar_items'] = self.toolbar_items

        # make sure that context has an id
        if "tag_id" not in context:
            context['tag_id'] = id_generator()

        # add the default css class if doesn't exists
        if "class" in context['attrs']:
            classes = context['attrs']['class'].split(" ")
            if self.css_class not in classes:
                classes.append(self.css_class)
                context['attrs']['class'] = " ".join(classes)
        else:
            context['attrs']['class'] = self.css_class

        return context

    def render(self, name, value, attrs=None):
        """returns the html of wysiwyg input"""
        context = self.get_context(name, value, attrs)
        return loader.render_to_string(
            self.template_name,
            context
        )

class SelectWidgetBootstrap(Select):
    """
    http://twitter.github.com/bootstrap/components.html#buttonDropdowns
    Needs bootstrap and jquery
    """
    js = ("""
    <script type="text/javascript">
        function setBtnGroupVal(elem) {
            btngroup = $(elem).parents('.btn-group');
            selected_a = btngroup.find('a[selected]');
            if (selected_a.length > 0) {
                val = selected_a.attr('data-value');
                label = selected_a.html();
            } else {
                btngroup.find('a').first().attr('selected', 'selected');
                setBtnGroupVal(elem);
            }
            btngroup.find('input').val(val);
            btngroup.find('.btn-group-label').html(label);
        }
        $(document).ready(function() {
            $('.btn-group-form input').each(function() {
                setBtnGroupVal(this);
            });
            $('.btn-group-form li a').click(function() {
                $(this).parent().siblings().find('a').attr('selected', false);
                $(this).attr('selected', true);
                setBtnGroupVal(this);
            });
        })
    </script>
    """)
    def __init__(self, attrs={'class': 'btn-group pull-left btn-group-form'}, choices=()):
        self.noscript_widget = Select(attrs={}, choices=choices)
        super(SelectWidgetBootstrap, self).__init__(attrs, choices)
    
    def __setattr__(self, k, value):
        super(SelectWidgetBootstrap, self).__setattr__(k, value)
        if k != 'attrs':
            self.noscript_widget.__setattr__(k, value)
    
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        output = ["""<div%(attrs)s>"""
                  """    <button class="btn btn-group-label" type="button">%(label)s</button>"""
                  """    <button class="btn dropdown-toggle" type="button" data-toggle="dropdown">"""
                  """        <span class="caret"></span>"""
                  """    </button>"""
                  """    <ul class="dropdown-menu">"""
                  """        %(options)s"""
                  """    </ul>"""
                  """    <input type="hidden" name="%(name)s" value="" class="btn-group-value" />"""
                  """</div>"""
                  """%(js)s"""
                  """<noscript>%(noscript)s</noscript>"""
                   % {'attrs': flatatt(final_attrs),
                      'options':self.render_options(choices, [value]),
                      'label': _(u'Select an option'),
                      'name': name,
                      'js': SelectWidgetBootstrap.js,
                      'noscript': self.noscript_widget.render(name, value, {}, choices)} ]
        return mark_safe(u'\n'.join(output))

    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_unicode(option_value)
        selected_html = (option_value in selected_choices) and u' selected="selected"' or ''
        return u'<li><a href="javascript:void(0)" data-value="%s"%s>%s</a></li>' % (
            escape(option_value), selected_html,
            conditional_escape(force_unicode(option_label)))

    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        selected_choices = set([force_unicode(v) for v in selected_choices])
        output = []
        for option_value, option_label in chain(self.choices, choices):
            if isinstance(option_label, (list, tuple)):
                output.append(u'<li class="divider" label="%s"></li>' % escape(force_unicode(option_value)))
                for option in option_label:
                    output.append(self.render_option(selected_choices, *option))
            else:
                output.append(self.render_option(selected_choices, option_value, option_label))
        return u'\n'.join(output)