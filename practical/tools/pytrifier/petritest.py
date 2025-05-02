'''
Created on Aug 24, 2011

@author: crash
'''
import unittest
import petrinet as pn


class TestPetriNet(unittest.TestCase):


    def setUp(self):
        
        '''
        1 (pre-places)
        o
        |
        x 2
        |
        o
        3 (post-places)
        '''      
        self.simple = pn.PetriNet()
        self.simple.add_place(1)
        self.simple.add_transition(2)
        self.simple.add_place(3)
        self.simple.add_edge(1, 2)
        self.simple.add_edge(2, 3)
        
        '''
        11 12 13
        o  o  o
         \ | / 
           x 2
         / | \ 
        o  o  o
        31 32 33
        '''        
        self.multiple = pn.PetriNet()
        self.multiple.add_place(11)
        self.multiple.add_place(12)
        self.multiple.add_place(13)
        self.multiple.add_transition(2)
        self.multiple.add_place(31)
        self.multiple.add_place(32)
        self.multiple.add_place(33)
        self.multiple.add_edge(11, 2, weight=1)
        self.multiple.add_edge(12, 2, weight=2)
        self.multiple.add_edge(13, 2, weight=3)
        self.multiple.add_edge(2, 31, weight=3)
        self.multiple.add_edge(2, 32, weight=2)
        self.multiple.add_edge(2, 33, weight=1)
        
        '''
                11
                o
                |
                x 21
          12 13 |
          o  o  o 14
          \ /\ /
        22 x  x 23
           |  |
           o  o
           31 32
        '''
        self.confusion = pn.PetriNet()
        self.confusion.add_place(11)
        self.confusion.add_place(12)
        self.confusion.add_place(13)
        self.confusion.add_place(14)
        self.confusion.add_transition(21)
        self.confusion.add_transition(22)
        self.confusion.add_transition(23)
        self.confusion.add_place(31)
        self.confusion.add_place(32)
        self.confusion.add_edge(11, 21)
        self.confusion.add_edge(21, 14)
        self.confusion.add_edge(12, 22)
        self.confusion.add_edge(13, 22)
        self.confusion.add_edge(22, 31)
        self.confusion.add_edge(13, 23)
        self.confusion.add_edge(14, 23)
        self.confusion.add_edge(23, 32)

        '''
        1 (pre/post-place)
        o
        ||
        x 2
        |
        o
        3 (post-place)
        '''      
        self.loop = pn.PetriNet()
        self.loop.add_place(1)
        self.loop.add_transition(2)
        self.loop.add_place(3)
        self.loop.add_edge(1, 2)
        self.loop.add_edge(2, 1)
        self.loop.add_edge(2, 3)
        
        '''
             11     12
             o      o
            / \     |
        21 x  x 22  x 23
           |  |     |
           o  o     o
           31 32    33
        '''        
        self.conflict = pn.PetriNet(capacity=5000)
        self.conflict.add_place(11)
        self.conflict.add_place(12)
        self.conflict.add_transition(21)
        self.conflict.add_transition(22)
        self.conflict.add_transition(23)
        self.conflict.add_place(31)
        self.conflict.add_place(32)
        self.conflict.add_place(33)
        self.conflict.add_edge(11, 21)
        self.conflict.add_edge(11, 22)
        self.conflict.add_edge(12, 23)
        self.conflict.add_edge(21, 31)
        self.conflict.add_edge(22, 32)
        self.conflict.add_edge(23, 33)
        
        '''
             11
             o
            / \
        21 x  x 22
           |  |
           o  o
           31 32
        '''        
        self.strength = pn.PetriNet(capacity=5000)
        self.strength.add_place(11)
        self.strength.add_transition(21, strength=3)
        self.strength.add_transition(22, strength=2)
        self.strength.add_place(31)
        self.strength.add_place(32)
        self.strength.add_edge(11, 21)
        self.strength.add_edge(11, 22)
        self.strength.add_edge(21, 31)
        self.strength.add_edge(22, 32)
        
        
    def test_marking(self):
        marking = self.simple.marking(1)
        self.assertEqual(marking.keys(), self.simple.places())
        
        self.assertEqual(marking.values(), [1,1])
        
        marking = self.multiple.marking()
        self.assertEqual(marking.keys(), self.multiple.places())
        
        marking = self.confusion.marking()
        self.assertEqual(marking.keys(), self.confusion.places())
        
    def test_fire_transition(self):
        marking = {1: 1, 3: 2}
        self.assertTrue(self.simple.is_enabled(2, marking))
        result = self.simple.fire_transition(2, marking)
        self.assertDictEqual(result, {1: 0, 3: 3})
        self.assertFalse(self.simple.is_enabled(2, result))
        marking = {1: 4, 3: 5}
        self.assertTrue(self.simple.is_enabled(2, marking))
        result = self.simple.fire_transition(2, marking)
        self.assertDictEqual(result, {1: 3, 3: 6})
        self.assertFalse(self.simple.is_enabled(2, result))
        
        marking = {11: 1, 12: 2, 13: 4, 31: 2, 32: 3, 33: 3}
        self.assertTrue(self.multiple.is_enabled(2, marking))
        result = self.multiple.fire_transition(2, marking)
        self.assertDictEqual(result, {11: 0, 12: 0, 13: 1, 31: 5, 32: 5, 33: 4})
        self.assertFalse(self.multiple.is_enabled(2, result))
        marking = {11: 6, 12: 6, 13: 6, 31: 1, 32: 5, 33: 4}
        self.assertTrue(self.multiple.is_enabled(2, marking))
        result = self.multiple.fire_transition(2, marking)
        self.assertDictEqual(result, {11: 5, 12: 4, 13: 3, 31: 4, 32: 7, 33: 5})
        self.assertFalse(self.multiple.is_enabled(2, result))
        

        marking = {11: 1, 12: 1, 13: 1, 14: 0, 31: 1, 32: 1}
        self.assertTrue(self.confusion.is_enabled(21, marking))
        self.assertTrue(self.confusion.is_enabled(22, marking))
        self.assertFalse(self.confusion.is_enabled(23, marking))
        result = self.confusion.fire_transition(21, marking)
        self.assertFalse(self.confusion.is_enabled(21, result))
        self.assertTrue(self.confusion.is_enabled(23, result))
    
    def test_fire_step(self):
        marking = {11: 1, 12: 1, 13: 1, 14: 0, 31: 1, 32: 1}
        result, firing_sequence = self.confusion.fire_step(marking)
        self.assertDictEqual(result, {11: 0, 12: 0, 13: 0, 14: 1, 31: 2, 32: 1})
        firing_sequence.sort()
        self.assertEqual(firing_sequence, [21,22])
        self.assertEqual(self.confusion.fire_step(result),(None, None))
        
    def test_step_iter(self):
        marking = {11: 5, 12: 6, 13: 7, 14: 0, 31: 0, 32: 0}
        markings = [x for x,_ in self.confusion.step_iter(marking)]
        self.assertDictEqual(markings[-1:][0], {11: 0, 12: 0, 13: 0, 14: 4, 31: 6, 32: 1})
            
        marking = {1: 1, 3: 0}
        markings = [x for x,_ in self.loop.step_iter(marking)]
        self.assertDictEqual(markings[-6:][0], {1: 1, 3: 1})
        self.assertDictEqual(markings[-5:][0], {1: 1, 3: 2})
        self.assertDictEqual(markings[-4:][0], {1: 1, 3: 3})
        self.assertDictEqual(markings[-3:][0], {1: 1, 3: 4})
        self.assertDictEqual(markings[-2:][0], {1: 1, 3: 5})
        self.assertDictEqual(markings[-1:][0], {1: 1, 3: 6})
        
        marking = {1: 4, 3: 0}
        markings = [x for x,_ in self.loop.step_iter(marking)]
        self.assertDictEqual(markings[-2:][0], {1: 4, 3: 4})
        self.assertDictEqual(markings[-1:][0], {1: 4, 3: 6})
        
        marking = {11: 5000, 12: 0, 31: 0, 32: 0, 33: 5000}
        markings = [x for x,_ in self.conflict.step_iter(marking)]
        self.assertAlmostEqual(markings[-1:][0][31] / float(markings[-1:][0][32]), 1, delta=0.1)
        self.assertAlmostEqual(markings[-1:][0][31] / float(2500), 1, delta=0.1)
        self.assertAlmostEqual(markings[-1:][0][31] / float(markings[-1:][0][33]), 0.5, delta=0.1)
        
        marking = {11: 5000, 31: 0, 32: 0}
        markings = [x for x,_ in self.strength.step_iter(marking)]
        self.assertAlmostEqual(markings[-1:][0][31] / float(markings[-1:][0][32]), 3/2.0, delta=0.1)
        
    def test_simulate(self):
        pass

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()