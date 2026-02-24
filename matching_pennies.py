import numpy as np
import random


information_sets = {
    'P1':{
        'regret_sum': np.array([0.0,0.0]),
        'strategy_sum': np.array([0.0,0.0])
    },
    'P2':{
        'regret_sum': np.array([0.0,0.0]),
        'strategy_sum': np.array([0.0,0.0])
    },
}

def get_strategy(info_set:str):
    vector = information_sets[info_set]['regret_sum']
    vector_copy = vector.copy()
    vector_copy[vector_copy<0] = 0
    if vector_copy.sum() == 0:
        vector_copy[:] = 0.5
    vector_copy /= vector_copy.sum()
    return vector_copy

tree = {
    'node_type': 'decision',
    'player': 1,
    'info_set': 'P1',
    'children': {
        'H': {
            'node_type': 'decision',
            'player':2,
            'info_set':'P2',
            'children':{
                'H':{
                'node_type':'terminal',
                'payoff': +1,
            },
                'T':{
                'node_type':'terminal',
                'payoff': -1,
                },
            },},
        'T': {
            'node_type': 'decision',
            'player': 2,
            'info_set': 'P2',
            'children': {
                'H': {
                    'node_type': 'terminal',
                    'payoff': -1,
                },
                'T': {
                    'node_type': 'terminal',
                    'payoff': 1,
                }
            }
        }

    }
}

def cfr(node, reach_p1, reach_p2):
    if node['node_type']== 'terminal':
        return node['payoff']
    else:
        strategy = get_strategy(node['info_set'])
        node_payoff = 0.0
        action_payoffs = np.zeros(2)
        for i, action in enumerate(['H','T']):
            child = node['children'][action]
            if node['player'] == 1:
                child_payoff = cfr(child, reach_p1 * strategy[i], reach_p2)
            else:
                child_payoff = cfr(child, reach_p1, reach_p2 * strategy[i])
            action_payoffs[i] = child_payoff
            node_payoff += strategy[i]*child_payoff
        if node['player'] == 1:
            information_sets['P1']['regret_sum'] += reach_p2 * (action_payoffs - node_payoff)
            information_sets['P1']['strategy_sum'] += reach_p1 * strategy
        else:
            information_sets['P2']['regret_sum'] += reach_p1 * -(action_payoffs - node_payoff)
            information_sets['P2']['strategy_sum'] += reach_p2 * strategy

    return node_payoff

for i in range(2):
    cfr(tree,1.0,1.0)

s = information_sets['P1']['strategy_sum']
s_p = information_sets['P2']['strategy_sum']
average_strategy_1 = s/s.sum()
average_strategy_2 = s_p/s_p.sum()

print(average_strategy_1)
print(average_strategy_2)