
class PointCloudPreprocessor:
    def __init__(self, config):
        self.config = config

    def transform(self, points_np):
        # TODO: convert point cloud array to model input tensor
        """
        points_np: NumPy array containing point cloud fields.
        returns: NumPy array in the exact format expected by the pose model.
        """
        return points_np