import mock
import pandas as pd
import pytest
from six import PY3

from dtale.app import build_app
from dtale.dash_application.charts import (build_axes, build_spaced_ticks,
                                           chart_wrapper)
from dtale.dash_application.components import Wordcloud
from dtale.dash_application.views import (build_figure_data, chart_url_params,
                                          get_url_parser)

if PY3:
    from contextlib import ExitStack
else:
    from contextlib2 import ExitStack

URL = 'http://localhost:40000'
app = build_app(url=URL)


def ts_builder(input_id='input-data'):
    return {'id': input_id, 'property': 'modified_timestamp', 'value': 1579972492434}


def path_builder(port):
    return {'id': 'url', 'property': 'pathname', 'value': '/charts/{}'.format(port)}


@pytest.mark.unit
def test_display_page(unittest):
    import dtale.views as views

    df = pd.DataFrame(dict(a=[1, 2, 3], b=[4, 5, 6], c=[7, 8, 9]))
    with app.test_client() as c:
        with ExitStack() as stack:
            df, _ = views.format_data(df)
            stack.enter_context(mock.patch('dtale.dash_application.views.DATA', {c.port: df}))
            stack.enter_context(mock.patch('dtale.dash_application.charts.DATA', {c.port: df}))
            pathname = path_builder(c.port)
            params = {
                'output': 'popup-content.children',
                'changedPropIds': ['url.modified_timestamp'],
                'inputs': [{'id': 'url', 'property': 'modified_timestamp'}],
                'state': [pathname]
            }
            response = c.post('/charts/_dash-update-component', json=params)
            resp_data = response.get_json()['response']
            component_defs = resp_data['props']['children']['props']['children']
            x_dd = component_defs[8]['props']['children'][0]
            x_dd_options = x_dd['props']['children'][0]['props']['children'][1]['props']['options']
            unittest.assertEqual([dict(label=v, value=v) for v in ['a', 'b', 'c']], x_dd_options)


@pytest.mark.unit
def test_query_changes(unittest):
    import dtale.views as views

    df = pd.DataFrame(dict(a=[1, 2, 3], b=[4, 5, 6], c=[7, 8, 9]))
    with app.test_client() as c:
        with ExitStack() as stack:
            df, _ = views.format_data(df)
            stack.enter_context(mock.patch('dtale.dash_application.views.DATA', {c.port: df}))
            stack.enter_context(mock.patch('dtale.dash_application.charts.DATA', {c.port: df}))
            pathname = path_builder(c.port)
            params = {
                'output': '..query-data.data...query-input.style...query-input.title..',
                'changedPropIds': ['query-input.value'],
                'inputs': [{'id': 'query-input', 'property': 'value', 'value': 'd'}],
                'state': [pathname, {'id': 'query-data', 'property': 'data'}]
            }
            response = c.post('/charts/_dash-update-component', json=params)
            resp_data = response.get_json()['response']
            assert resp_data['query-data']['data'] is None
            assert resp_data['query-input']['title'] == "name 'd' is not defined"

            params['inputs'][0]['value'] = 'a == 1'
            response = c.post('/charts/_dash-update-component', json=params)
            resp_data = response.get_json()['response']
            assert resp_data['query-data']['data'] == 'a == 1'


@pytest.mark.unit
def test_input_changes(unittest):
    import dtale.views as views

    df = pd.DataFrame(dict(a=[1, 2, 3], b=[4, 5, 6], c=[7, 8, 9]))
    with app.test_client() as c:
        with ExitStack() as stack:
            df, _ = views.format_data(df)
            stack.enter_context(mock.patch('dtale.dash_application.views.DATA', {c.port: df}))
            stack.enter_context(mock.patch('dtale.dash_application.charts.DATA', {c.port: df}))
            pathname = path_builder(c.port)
            params = {
                'output': (
                    '..input-data.data...x-dropdown.options...y-dropdown.options...y-heatmap-dropdown.options.'
                    '..z-dropdown.options...group-dropdown.options..'
                ),
                'changedPropIds': ['chart-tabs.value'],
                'inputs': [
                    ts_builder('query-data'),
                    {'id': 'chart-tabs', 'property': 'value', 'value': 'line'},
                    {'id': 'x-dropdown', 'property': 'value'},
                    {'id': 'y-dropdown', 'property': 'value'},
                    {'id': 'y-heatmap-dropdown', 'property': 'value'},
                    {'id': 'z-dropdown', 'property': 'value'},
                    {'id': 'group-dropdown', 'property': 'value'},
                    {'id': 'agg-dropdown', 'property': 'value'},
                    {'id': 'window-input', 'property': 'value'},
                    {'id': 'rolling-comp-dropdown', 'property': 'value'}
                ],
                'state': [pathname, {'id': 'query-data', 'property': 'data'}]
            }
            response = c.post('/charts/_dash-update-component', json=params)
            resp_data = response.get_json()
            unittest.assertEqual(resp_data['response']['input-data']['data'], {
                'chart_type': 'line', 'x': None, 'y': [], 'z': None, 'group': None, 'agg': None, 'window': None,
                'rolling_comp': None, 'query': None
            })


@pytest.mark.unit
def test_chart_type_changes(unittest):
    with app.test_client() as c:
        fig_data_outputs = (
            '..y-input.style...y-heatmap-input.style...z-input.style...group-input.style...rolling-inputs.style...'
            'cpg-input.style...barmode-input.style...barsort-input.style...barsort-dropdown.options...'
            'yaxis-input.style...yaxis-dropdown.options..'
        )
        inputs = {'id': 'input-data', 'property': 'data', 'value': {
            'chart_type': 'line', 'x': 'a', 'y': ['b'], 'z': None, 'group': None, 'agg': None,
            'window': None, 'rolling_comp': None}}
        params = {
            'output': fig_data_outputs,
            'changedPropIds': ['input-data.modified_timestamp'],
            'inputs': [ts_builder()],
            'state': [inputs]
        }
        response = c.post('/charts/_dash-update-component', json=params)
        resp_data = response.get_json()['response']
        for id in ['z-input', 'rolling-inputs', 'cpg-input', 'barmode-input', 'barsort-input']:
            assert resp_data[id]['style']['display'] == 'none'
        for id in ['group-input', 'yaxis-input']:
            assert resp_data[id]['style']['display'] == 'block'
        unittest.assertEqual([o['value'] for o in resp_data['barsort-dropdown']['options']], ['a', 'b'])
        unittest.assertEqual([o['value'] for o in resp_data['yaxis-dropdown']['options']], ['b'])

        inputs['value']['chart_type'] = 'bar'
        inputs['value']['y'] = ['b', 'c']
        params = {
            'output': fig_data_outputs,
            'changedPropIds': ['input-data.modified_timestamp'],
            'inputs': [ts_builder()],
            'state': [inputs]
        }
        response = c.post('/charts/_dash-update-component', json=params)
        resp_data = response.get_json()['response']
        assert resp_data['barmode-input']['style']['display'] == 'block'
        assert resp_data['barsort-input']['style']['display'] == 'block'

        inputs['value']['chart_type'] = 'line'
        inputs['value']['y'] = ['b']
        inputs['value']['group'] = ['c']
        params = {
            'output': fig_data_outputs,
            'changedPropIds': ['input-data.modified_timestamp'],
            'inputs': [ts_builder()],
            'state': [inputs]
        }
        response = c.post('/charts/_dash-update-component', json=params)
        resp_data = response.get_json()['response']
        assert resp_data['cpg-input']['style']['display'] == 'block'

        inputs['value']['chart_type'] = 'heatmap'
        inputs['value']['group'] = None
        inputs['value']['z'] = 'c'
        params = {
            'output': fig_data_outputs,
            'changedPropIds': ['input-data.modified_timestamp'],
            'inputs': [ts_builder()],
            'state': [inputs]
        }
        response = c.post('/charts/_dash-update-component', json=params)
        resp_data = response.get_json()['response']
        assert resp_data['z-input']['style']['display'] == 'block'


@pytest.mark.unit
def test_yaxis_changes(unittest):
    with app.test_client() as c:
        params = dict(
            output='..yaxis-min-input.value...yaxis-max-input.value..',
            changedPropIds=['yaxis-dropdown.value'],
            inputs=[{'id': 'yaxis-dropdown', 'property': 'value'}],
            state=[
                dict(id='input-data', property='data', value=dict(chart_type='line', x='a', y=['b'])),
                dict(id='yaxis-data', property='data', value=dict(yaxis={})),
                dict(id='range-data', property='data', value=dict(min={'b': 4}, max={'b': 6}))
            ]
        )
        response = c.post('/charts/_dash-update-component', json=params)
        resp_data = response.get_json()
        unittest.assertEquals(resp_data['response'], {
            'yaxis-min-input': {'value': None}, 'yaxis-max-input': {'value': None}
        })

        params['state'][0]['value']['y'] = None
        response = c.post('/charts/_dash-update-component', json=params)
        resp_data = response.get_json()
        unittest.assertEquals(resp_data['response'], {
            'yaxis-min-input': {'value': None}, 'yaxis-max-input': {'value': None}
        })

        params['state'][0]['value']['y'] = ['b']
        params['inputs'][0]['value'] = 'b'
        response = c.post('/charts/_dash-update-component', json=params)
        resp_data = response.get_json()
        unittest.assertEquals(resp_data['response'], {
            'yaxis-min-input': {'value': 4}, 'yaxis-max-input': {'value': 6}
        })

        params['state'][0]['value']['chart_type'] = 'heatmap'
        response = c.post('/charts/_dash-update-component', json=params)
        resp_data = response.get_json()
        unittest.assertEquals(resp_data['response'], {
            'yaxis-min-input': {'value': None}, 'yaxis-max-input': {'value': None}
        })


@pytest.mark.unit
def test_chart_input_updates(unittest):
    with app.test_client() as c:
        params = {
            'output': 'chart-input-data.data',
            'changedPropIds': ['cpg-toggle.on'],
            'inputs': [
                {'id': 'cpg-toggle', 'property': 'on', 'value': False},
                {'id': 'barmode-dropdown', 'property': 'value', 'value': 'group'},
                {'id': 'barsort-dropdown', 'property': 'value'},
            ],
        }

        response = c.post('/charts/_dash-update-component', json=params)
        resp_data = response.get_json()
        unittest.assertEqual(resp_data['response']['props']['data'], {
            'cpg': False, 'barmode': 'group', 'barsort': None
        })


@pytest.mark.unit
def test_yaxis_data(unittest):
    with app.test_client() as c:
        params = {
            'output': 'yaxis-data.data',
            'changedPropIds': ['yaxis-min-input.value'],
            'inputs': [
                {'id': 'yaxis-min-input', 'property': 'value', 'value': -1.52},
                {'id': 'yaxis-max-input', 'property': 'value', 'value': 0.42}
            ],
            'state': [
                {'id': 'yaxis-dropdown', 'property': 'value', 'value': 'Col1'},
                {'id': 'yaxis-data', 'property': 'data', 'value': {}},
                {'id': 'range-data', 'property': 'data', 'value': {'min': {'Col1': -0.52}, 'max': {'Col1': 0.42}}}
            ]
        }
        response = c.post('/charts/_dash-update-component', json=params)
        resp_data = response.get_json()
        unittest.assertEqual(resp_data['response']['props']['data'], {'Col1': {'min': -1.52, 'max': 0.42}})

        params['inputs'][1]['value'] = 1.42
        params['state'][1]['value'] = {'Col1': {'min': -1.52, 'max': 0.42}}
        response = c.post('/charts/_dash-update-component', json=params)
        resp_data = response.get_json()
        unittest.assertEqual(resp_data['response']['props']['data'], {'Col1': {'min': -1.52, 'max': 1.42}})

        params['inputs'][0]['value'] = -0.52
        params['inputs'][1]['value'] = 0.42
        params['state'][1]['value'] = {'Col1': {'min': -1.52, 'max': 1.42}}
        response = c.post('/charts/_dash-update-component', json=params)
        resp_data = response.get_json()
        unittest.assertEqual(resp_data['response']['props']['data'], {})

        params['state'][0]['value'] = None
        response = c.post('/charts/_dash-update-component', json=params)
        assert response.get_json() is None

        params['state'][0]['value'] = 'Col1'


def build_chart_params(pathname, inputs={}, chart_inputs={}, yaxis={}, last_inputs={}):
    return {
        'output': '..chart-content.children...last-chart-input-data.data...range-data.data..',
        'changedPropIds': ['input-data.modified_timestamp'],
        'inputs': [ts_builder('input-data'), ts_builder('chart-input-data'), ts_builder('yaxis-data')],
        'state': [
            pathname,
            {'id': 'input-data', 'property': 'data', 'value': inputs},
            {'id': 'chart-input-data', 'property': 'data', 'value': chart_inputs},
            {'id': 'yaxis-data', 'property': 'data', 'value': yaxis},
            {'id': 'last-chart-input-data', 'property': 'data', 'value': last_inputs}
        ]
    }


@pytest.mark.unit
def test_chart_building_nones(unittest):

    with app.test_client() as c:
        pathname = path_builder(c.port)

        params = build_chart_params(pathname)
        response = c.post('/charts/_dash-update-component', json=params)
        resp_data = response.get_json()
        assert resp_data['response']['chart-content']['children'] is None

        params['state'][2]['value'] = {'cpg': False, 'barmode': 'group', 'barsort': None}
        params['state'][-1]['value'] = {'cpg': False, 'barmode': 'group', 'barsort': None, 'yaxis': {}}
        response = c.post('/charts/_dash-update-component', json=params)
        assert response.get_json() is None


@pytest.mark.unit
def test_chart_building_wordcloud(unittest):
    import dtale.views as views

    df = pd.DataFrame(dict(a=[1, 2, 3], b=[4, 5, 6], c=[7, 8, 9]))
    with app.test_client() as c:
        with ExitStack() as stack:
            df, _ = views.format_data(df)
            stack.enter_context(mock.patch('dtale.dash_application.views.DATA', {c.port: df}))
            stack.enter_context(mock.patch('dtale.dash_application.charts.DATA', {c.port: df}))
            pathname = path_builder(c.port)
            inputs = {
                'chart_type': 'wordcloud', 'x': 'a', 'y': ['b'], 'z': None, 'group': None, 'agg': None,
                'window': None, 'rolling_comp': None
            }
            chart_inputs = {'cpg': False, 'barmode': 'group', 'barsort': None}
            params = build_chart_params(pathname, inputs, chart_inputs)
            response = c.post('/charts/_dash-update-component', json=params)
            resp_data = response.get_json()['response']
            assert resp_data['chart-content']['children']['props']['children'][1]['type'] == 'Wordcloud'


@pytest.mark.unit
def test_chart_building_scatter(unittest):
    import dtale.views as views

    df = pd.DataFrame(dict(a=[1, 2, 3], b=[4, 5, 6], c=[7, 8, 9]))
    with app.test_client() as c:
        with ExitStack() as stack:
            df, _ = views.format_data(df)
            stack.enter_context(mock.patch('dtale.dash_application.views.DATA', {c.port: df}))
            stack.enter_context(mock.patch('dtale.dash_application.charts.DATA', {c.port: df}))
            pathname = path_builder(c.port)
            inputs = {
                'chart_type': 'scatter', 'x': 'a', 'y': ['b'], 'z': None, 'group': None, 'agg': None,
                'window': None, 'rolling_comp': None
            }
            chart_inputs = {'cpg': False, 'barmode': 'group', 'barsort': None}
            params = build_chart_params(pathname, inputs, chart_inputs)
            response = c.post('/charts/_dash-update-component', json=params)
            resp_data = response.get_json()['response']
            assert resp_data['chart-content']['children'][0]['props']['children'][1]['props']['id'] == 'scatter-all-b'

            inputs['y'] = ['b']
            inputs['group'] = ['c']
            chart_inputs['cpg'] = True
            params = build_chart_params(pathname, inputs, chart_inputs)
            response = c.post('/charts/_dash-update-component', json=params)
            resp_data = response.get_json()['response']
            assert len(resp_data['chart-content']['children']) == 2


@pytest.mark.unit
def test_chart_building_bar_and_popup(unittest):
    import dtale.views as views

    df = pd.DataFrame(dict(a=[1, 2, 3], b=[4, 5, 6], c=[7, 8, 9]))
    with app.test_client() as c:
        with ExitStack() as stack:
            df, _ = views.format_data(df)
            stack.enter_context(mock.patch('dtale.dash_application.views.DATA', {c.port: df}))
            stack.enter_context(mock.patch('dtale.dash_application.charts.DATA', {c.port: df}))
            pathname = path_builder(c.port)
            inputs = {
                'chart_type': 'bar', 'x': 'a', 'y': ['b', 'c'], 'z': None, 'group': None, 'agg': None,
                'window': None, 'rolling_comp': None
            }
            chart_inputs = {'cpg': False, 'barmode': 'group', 'barsort': None}
            params = build_chart_params(pathname, inputs, chart_inputs)
            response = c.post('/charts/_dash-update-component', json=params)
            resp_data = response.get_json()['response']
            url = resp_data['chart-content']['children']['props']['children'][0]['props']['href']
            assert url.startswith('/charts/popup/{}?'.format(c.port))
            url_params = dict(get_url_parser()(url.split('?')[-1]))
            unittest.assertEqual(
                url_params,
                {'chart_type': 'bar', 'x': 'a', 'barmode': 'group', 'cpg': 'false', 'y': '["b", "c"]'}
            )
            unittest.assertEqual(
                resp_data['chart-content']['children']['props']['children'][1]['props']['figure']['layout'],
                {'barmode': 'group',
                 'title': {'text': 'b, c by a'},
                 'xaxis': {'tickformat': '.0f'},
                 'yaxis': {'title': {'text': 'b'}, 'tickformat': '.0f'},
                 'yaxis2': {'anchor': 'x', 'overlaying': 'y', 'side': 'right', 'title': {'text': 'c'},
                            'tickformat': '.0f'}}
            )

            response = c.get(url)
            assert response.status_code == 200
            [pathname_val, search_val] = url.split('?')
            response = c.post('/charts/_dash-update-component', json={
                'output': 'popup-content.children',
                'changedPropIds': ['url.modified_timestamp'],
                'inputs': [{'id': 'url', 'property': 'modified_timestamp'}],
                'state': [{'id': 'url', 'property': 'pathname', 'value': pathname_val}]
            })
            assert response.status_code == 200
            response = c.post('/charts/_dash-update-component', json={
                'output': 'popup-chart-content.children',
                'changedPropIds': [],
                'inputs': [
                    {'id': 'url', 'property': 'pathname', 'value': pathname_val},
                    {'id': 'url', 'property': 'search', 'value': '?{}'.format(search_val)}
                ]
            })
            resp_data = response.get_json()['response']
            unittest.assertEqual(
                resp_data['props']['children']['props']['children'][1]['props']['figure']['layout'],
                {'barmode': 'group',
                 'title': {'text': 'b, c by a'},
                 'xaxis': {'tickformat': '.0f'},
                 'yaxis': {'title': {'text': 'b'}, 'tickformat': '.0f'},
                 'yaxis2': {'anchor': 'x', 'overlaying': 'y', 'side': 'right', 'title': {'text': 'c'},
                            'tickformat': '.0f'}}
            )

            chart_inputs['barmode'] = 'stack'
            params = build_chart_params(pathname, inputs, chart_inputs)
            response = c.post('/charts/_dash-update-component', json=params)
            resp_data = response.get_json()['response']
            unittest.assertEqual(
                resp_data['chart-content']['children']['props']['children'][1]['props']['figure']['layout'],
                {'barmode': 'stack',
                 'title': {'text': 'b, c by a'},
                 'xaxis': {'tickformat': '.0f'},
                 'yaxis': {'tickformat': '.0f', 'title': {'text': 'b'}}}
            )

            chart_inputs['barmode'] = 'group'
            chart_inputs['barsort'] = 'b'
            params = build_chart_params(pathname, inputs, chart_inputs)
            response = c.post('/charts/_dash-update-component', json=params)
            resp_data = response.get_json()['response']
            unittest.assertEqual(
                resp_data['chart-content']['children']['props']['children'][1]['props']['figure']['layout'],
                {'barmode': 'group',
                 'title': {'text': 'b, c by a'},
                 'xaxis': {'tickmode': 'array', 'ticktext': [1, 2, 3], 'tickvals': [0, 1, 2], 'tickformat': '.0f'},
                 'yaxis': {'title': {'text': 'b'}, 'tickformat': '.0f'},
                 'yaxis2': {'anchor': 'x', 'overlaying': 'y', 'side': 'right', 'title': {'text': 'c'},
                            'tickformat': '.0f'}}
            )

            inputs['y'] = ['b']
            inputs['group'] = ['c']
            chart_inputs['cpg'] = True
            params = build_chart_params(pathname, inputs, chart_inputs)
            response = c.post('/charts/_dash-update-component', json=params)
            resp_data = response.get_json()['response']
            assert len(resp_data['chart-content']['children']) == 2


@pytest.mark.unit
def test_chart_building_line(unittest):
    import dtale.views as views

    df = pd.DataFrame(dict(a=[1, 2, 3], b=[4, 5, 6], c=[7, 8, 9]))
    with app.test_client() as c:
        with ExitStack() as stack:
            df, _ = views.format_data(df)
            stack.enter_context(mock.patch('dtale.dash_application.views.DATA', {c.port: df}))
            stack.enter_context(mock.patch('dtale.dash_application.charts.DATA', {c.port: df}))
            pathname = path_builder(c.port)
            inputs = {
                'chart_type': 'line', 'x': 'a', 'y': ['b'], 'z': None, 'group': ['c'], 'agg': None,
                'window': None, 'rolling_comp': None
            }
            chart_inputs = {'cpg': True, 'barmode': 'group', 'barsort': 'b'}
            params = build_chart_params(pathname, inputs, chart_inputs)
            response = c.post('/charts/_dash-update-component', json=params)
            resp_data = response.get_json()['response']
            assert len(resp_data['chart-content']['children']) == 2

            inputs['group'] = None
            chart_inputs['cpg'] = False
            params = build_chart_params(pathname, inputs, chart_inputs)
            response = c.post('/charts/_dash-update-component', json=params)
            resp_data = response.get_json()['response']
            assert resp_data['chart-content']['children']['type'] == 'Div'


@pytest.mark.unit
def test_chart_building_heatmap(unittest, test_data):
    import dtale.views as views

    df = pd.DataFrame(dict(a=[1, 2, 3], b=[4, 5, 6], c=[7, 8, 9]))
    with app.test_client() as c:
        with ExitStack() as stack:
            df, _ = views.format_data(df)
            stack.enter_context(mock.patch('dtale.dash_application.views.DATA', {c.port: df}))
            stack.enter_context(mock.patch('dtale.dash_application.charts.DATA', {c.port: df}))
            pathname = path_builder(c.port)
            inputs = {
                'chart_type': 'heatmap', 'x': 'a', 'y': ['b'], 'z': 'c', 'group': None, 'agg': None,
                'window': None, 'rolling_comp': None
            }
            chart_inputs = {'cpg': False, 'barmode': 'group', 'barsort': 'b'}
            params = build_chart_params(pathname, inputs, chart_inputs)
            response = c.post('/charts/_dash-update-component', json=params)
            resp_data = response.get_json()['response']
            unittest.assertEqual(
                resp_data['chart-content']['children'][0]['props']['children'][1]['props']['figure']['layout']['title'],
                {'text': 'a vs b weighted by c'}
            )

    with app.test_client() as c:
        with ExitStack() as stack:
            df, _ = views.format_data(test_data)
            stack.enter_context(mock.patch('dtale.dash_application.views.DATA', {c.port: df}))
            stack.enter_context(mock.patch('dtale.dash_application.charts.DATA', {c.port: df}))
            pathname = path_builder(c.port)
            inputs = {
                'chart_type': 'heatmap', 'x': 'date', 'y': ['security_id'], 'z': 'bar', 'group': None, 'agg': 'mean',
                'window': None, 'rolling_comp': None
            }
            chart_inputs = {'cpg': False, 'barmode': 'group', 'barsort': 'b'}
            params = build_chart_params(pathname, inputs, chart_inputs)
            response = c.post('/charts/_dash-update-component', json=params)
            resp_data = response.get_json()['response']
            unittest.assertEqual(
                resp_data['chart-content']['children'][0]['props']['children'][1]['props']['figure']['layout']['title'],
                {'text': 'date vs security_id weighted by bar'}
            )


@pytest.mark.unit
def test_load_chart_error(unittest):
    import dtale.views as views

    df = pd.DataFrame(dict(a=[1, 2, 3], b=[4, 5, 6], c=[7, 8, 9]))
    with app.test_client() as c:
        with ExitStack() as stack:
            df, _ = views.format_data(df)
            stack.enter_context(mock.patch('dtale.dash_application.views.DATA', {c.port: df}))
            stack.enter_context(mock.patch('dtale.dash_application.charts.DATA', {c.port: df}))

            def build_chart_data_mock(data, x, y, group_col=None, agg=None, allow_duplicates=False, **kwargs):
                raise Exception('error test')
            stack.enter_context(mock.patch(
                'dtale.dash_application.views.build_chart_data',
                side_effect=build_chart_data_mock
            ))
            pathname = {'id': 'url', 'property': 'pathname', 'value': '/charts/{}'.format(c.port)}
            inputs = {'id': 'input-data', 'property': 'data', 'value': {
                'chart_type': 'line', 'x': 'a', 'y': ['b'], 'z': None, 'group': None, 'agg': None,
                'window': None, 'rolling_comp': None}}
            chart_inputs = {
                'id': 'chart-input-data', 'property': 'data', 'value': {
                    'cpg': False, 'barmode': 'group', 'barsort': None
                }
            }
            params = {
                'output': '..chart-content.children...last-chart-input-data.data...range-data.data..',
                'changedPropIds': ['input-data.modified_timestamp'],
                'inputs': [ts_builder('input-data'), ts_builder('chart-input-data'), ts_builder('yaxis-data')],
                'state': [
                    pathname,
                    inputs,
                    chart_inputs,
                    {'id': 'yaxis-data', 'property': 'data', 'value': {}},
                    {'id': 'last-chart-input-data', 'property': 'data', 'value': {}}
                ]
            }
            response = c.post('/charts/_dash-update-component', json=params)
            resp_data = response.get_json()['response']['chart-content']['children']
            assert resp_data['props']['children'][1]['props']['children'] == 'error test'


@pytest.mark.unit
def test_display_error(unittest):
    import dtale.views as views

    df = pd.DataFrame(dict(a=[1, 2, 3], b=[4, 5, 6], c=[7, 8, 9]))
    with app.test_client() as c:
        with ExitStack() as stack:
            df, _ = views.format_data(df)
            stack.enter_context(mock.patch('dtale.dash_application.views.DATA', {c.port: df}))
            stack.enter_context(mock.patch(
                'dtale.dash_application.components.Wordcloud',
                mock.Mock(side_effect=Exception('error test'))
            ))
            pathname = {'id': 'url', 'property': 'pathname', 'value': '/charts/{}'.format(c.port)}
            inputs = {'id': 'input-data', 'property': 'data', 'value': {
                'chart_type': 'wordcloud', 'x': 'a', 'y': ['b'], 'z': None, 'group': None, 'agg': None,
                'window': None, 'rolling_comp': None}}
            chart_inputs = {
                'id': 'chart-input-data', 'property': 'data', 'value': {
                    'cpg': False, 'barmode': 'group', 'barsort': None
                }
            }
            params = {
                'output': '..chart-content.children...last-chart-input-data.data...range-data.data..',
                'changedPropIds': ['input-data.modified_timestamp'],
                'inputs': [ts_builder('input-data'), ts_builder('chart-input-data'), ts_builder('yaxis-data')],
                'state': [
                    pathname,
                    inputs,
                    chart_inputs,
                    {'id': 'yaxis-data', 'property': 'data', 'value': {}},
                    {'id': 'last-chart-input-data', 'property': 'data', 'value': {}}
                ]
            }
            response = c.post('/charts/_dash-update-component', json=params)
            print(response.get_json())
            resp_data = response.get_json()['response']['chart-content']['children']
            assert resp_data['props']['children'][1]['props']['children'] == 'error test'

            params = {
                'output': '..chart-content.children...last-chart-input-data.data...range-data.data..',
                'changedPropIds': ['input-data.modified_timestamp'],
                'inputs': [ts_builder('input-data'), ts_builder('chart-input-data'), ts_builder('yaxis-data')],
                'state': [
                    pathname,
                    inputs,
                    chart_inputs,
                    {'id': 'yaxis-data', 'property': 'data', 'value': {}},
                    {'id': 'last-chart-input-data', 'property': 'data', 'value': {}}
                ]
            }
            response = c.post('/charts/_dash-update-component', json=params)
            resp_data = response.get_json()['response']['chart-content']['children']
            assert resp_data['props']['children'][1]['props']['children'] == 'error test'


@pytest.mark.unit
def test_build_axes(unittest):
    df = pd.DataFrame(dict(a=[1, 2, 3], b=[1, 2, 3], c=[4, 5, 6], d=[8, 9, 10], e=[11, 12, 13], f=[14, 15, 16]))
    with mock.patch('dtale.dash_application.charts.DATA', {'1': df}):
        y = ['b', 'c', 'd']
        yaxis_data = dict(b=dict(min=1, max=4), c=dict(min=5, max=7), d=dict(min=8, max=10))
        mins = dict(b=2, c=5, d=8)
        maxs = dict(b=4, c=6, d=10)
        axes = build_axes('1', 'a', yaxis_data, mins, maxs)(y)
        unittest.assertEqual(axes, {
            'yaxis': {'title': 'b', 'range': [1, 4], 'tickformat': '.0f'},
            'yaxis2': {'title': 'c', 'overlaying': 'y', 'side': 'right', 'anchor': 'x', 'range': [5, 7],
                       'tickformat': '.0f'},
            'yaxis3': {'title': 'd', 'overlaying': 'y', 'side': 'left', 'anchor': 'free', 'position': 0.05,
                       'tickformat': '.0f'},
            'xaxis': {'domain': [0.1, 1], 'tickformat': '.0f'}
        })

        y.append('e')
        yaxis_data['e'] = dict(min=11, max=13)
        mins['e'] = 11
        maxs['e'] = 13
        axes = build_axes('1', 'a', yaxis_data, mins, maxs)(y)
        unittest.assertEqual(axes, {
            'yaxis': {'title': 'b', 'range': [1, 4], 'tickformat': '.0f'},
            'yaxis2': {'title': 'c', 'overlaying': 'y', 'side': 'right', 'anchor': 'x', 'range': [5, 7],
                       'tickformat': '.0f'},
            'yaxis3': {'title': 'd', 'overlaying': 'y', 'side': 'left', 'anchor': 'free', 'position': 0.05,
                       'tickformat': '.0f'},
            'yaxis4': {'title': 'e', 'overlaying': 'y', 'side': 'right', 'anchor': 'free', 'position': 0.95,
                       'tickformat': '.0f'},
            'xaxis': {'domain': [0.1, 0.8999999999999999], 'tickformat': '.0f'}
        })

        y.append('f')
        yaxis_data['f'] = dict(min=14, max=17)
        mins['f'] = 14
        maxs['f'] = 17
        axes = build_axes('1', 'a', yaxis_data, mins, maxs)(y)
        unittest.assertEqual(axes, {
            'yaxis': {'title': 'b', 'range': [1, 4], 'tickformat': '.0f'},
            'yaxis2': {'title': 'c', 'overlaying': 'y', 'side': 'right', 'anchor': 'x', 'range': [5, 7],
                       'tickformat': '.0f'},
            'yaxis3': {'title': 'd', 'overlaying': 'y', 'side': 'left', 'anchor': 'free', 'position': 0.05,
                       'tickformat': '.0f'},
            'yaxis4': {'title': 'e', 'overlaying': 'y', 'side': 'right', 'anchor': 'free', 'position': 0.95,
                       'tickformat': '.0f'},
            'yaxis5': {'title': 'f', 'overlaying': 'y', 'side': 'left', 'anchor': 'free', 'position': 0.1,
                       'tickformat': '.0f'},
            'xaxis': {'domain': [0.15000000000000002, 0.8999999999999999], 'tickformat': '.0f'}
        })


@pytest.mark.unit
def test_build_figure_data(unittest):
    assert build_figure_data('/charts/1', x=None) is None
    assert build_figure_data('/charts/1', x='a', y=['b'], chart_type='heatmap') is None
    with mock.patch('dtale.dash_application.views.DATA', {}):
        fig_data = build_figure_data('/charts/1', x='a', y=['b'], chart_type='line')
        assert 'error' in fig_data and 'traceback' in fig_data


@pytest.mark.unit
def test_chart_wrapper(unittest):
    assert chart_wrapper('1', None)('foo') == 'foo'
    url_params = dict(chart_type='line', y=['b', 'c'], yaxis={'b': {'min': 3, 'max': 6}, 'd': {'min': 7, 'max': 10}},
                      agg='rolling', window=10, rolling_calc='corr')
    cw = chart_wrapper('1', dict(min={'b': 4}, max={'b': 6}), url_params)
    output = cw('foo')
    url_params = chart_url_params('?{}'.format(output.children[0].href.split('?')[-1]))
    unittest.assertEqual(url_params, {'chart_type': 'line', 'agg': 'rolling', 'window': 10, 'cpg': False,
                                      'y': ['b', 'c'], 'yaxis': {'b': {'min': 3, 'max': 6}}})


@pytest.mark.unit
def test_build_spaced_ticks(unittest):
    ticks = range(50)
    cfg = build_spaced_ticks(ticks, ticks)
    print(cfg['tickvals'])
    assert len(cfg['tickvals']) == 26


@pytest.mark.unit
def test_wordcloud():
    with pytest.raises(Exception) as error:
        Wordcloud('foo', {}, y='b', invalid_arg='blah')
    assert str(error).endswith(
        'TypeError: The `Wordcloud` component with the ID "foo" received an unexpected keyword argument: `invalid_arg`'
    )

    with pytest.raises(Exception) as error:
        Wordcloud(data={}, y='b', invalid_arg='blah')
    assert str(error).endswith('TypeError: Required argument `id` was not specified.')


@pytest.mark.unit
def test_build_chart_type():
    from dtale.dash_application.charts import build_chart

    import dtale.views as views

    with app.test_client() as c:
        with ExitStack() as stack:
            df, _ = views.format_data(pd.DataFrame(dict(a=[1, 2, 3], b=[4, 5, 6], c=[7, 8, 9])))
            stack.enter_context(mock.patch('dtale.dash_application.charts.DATA', {c.port: df}))
            with pytest.raises(NotImplementedError):
                build_chart(dict(min=None, max=None), c.port, chart_type='unknown')
