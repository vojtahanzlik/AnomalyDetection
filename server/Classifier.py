import pickle
from abc import abstractmethod, ABC

import torch
from PROD.models.featureClassifier import featureClassifier
from PROD.models.deviationClassifier import deviationClassifier
from helpers import get_logger

logger = get_logger("ClassifierFactory")


class ClassifierFactory:

    @staticmethod
    def load_classifier(path: str):
        classifier = None
        if path.endswith(".pkl"):
            with open(path, 'rb') as f:
                loaded_object = pickle.load(f)
                classifier = loaded_object
                if type(classifier) is featureClassifier:
                    classifier = FeatureClassifier(classifier)

                elif type(classifier) is deviationClassifier:
                    classifier = DeviationClassifier(classifier)
                else:
                    raise ValueError("Unknown classifier type in .pkl file")

        elif path.endswith(".pth"):
            classifier = torch.load(path)
            classifier = LstmClassifier(classifier)
        else:
            raise ValueError("Unsupported file extension")

        if classifier:
            logger.info(f"Loaded classifier: {classifier.__class__.__name__}")
        return classifier


class ClassifierBase(ABC):

    def __init__(self, classifier):
        self.classifier = classifier

    @abstractmethod
    def predict(self, signal) -> bool:
        pass


class FeatureClassifier(ClassifierBase):

    def predict(self, signal) -> bool:
        return self.classifier.predict_partial_signal(signal)


class DeviationClassifier(ClassifierBase):

    def predict(self, signal) -> bool:
        return self.classifier.predict_partial_signal(signal, vis=False)


class LstmClassifier(ClassifierBase):

    def predict(self, signal) -> bool:
        return self.classifier.predict(signal)
