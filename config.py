import json
import os

class Config:
    """
    Configuration class for the GPT-4o-mini model.
    This class holds all the necessary configurations for the model.
    """

    def __init__(self):
        self.model_name = "gpt-4o-mini"
        self.default_params = {
            "max_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "num_return_sequences": 1,
            "stop_sequences": None,
        }

    def to_dict(self):
        """
        Convert the configuration to a dictionary.
        """
        return {
            "model_name": self.model_name,
            "default_params": self.default_params
        }

    def save_to_file(self, file_path):
        """
        Save the configuration to a JSON file.

        Args:
            file_path (str): The path to the file where the configuration will be saved.
        """
        try:
            with open(file_path, 'w') as json_file:
                json.dump(self.to_dict(), json_file, indent=4)
            print(f"Configuration saved to {file_path}")
        except IOError as e:
            print(f"Error saving configuration to file: {e}")

    @classmethod
    def load_from_file(cls, file_path):
        """
        Load the configuration from a JSON file.

        Args:
            file_path (str): The path to the file from which the configuration will be loaded.

        Returns:
            Config: An instance of the Config class with loaded parameters.
        """
        if not os.path.exists(file_path):
            print(f"Configuration file {file_path} does not exist.")
            return cls()  # Return default config if file does not exist

        try:
            with open(file_path, 'r') as json_file:
                config_data = json.load(json_file)
                config = cls()
                config.model_name = config_data.get("model_name", config.model_name)
                config.default_params = config_data.get("default_params", config.default_params)
                return config
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading configuration from file: {e}")
            return cls()  # Return default config on error

# Example usage
if __name__ == "__main__":
    config = Config()
    config.save_to_file("gpt4o_mini_config.json")

    loaded_config = Config.load_from_file("gpt4o_mini_config.json")
    print(loaded_config.to_dict())