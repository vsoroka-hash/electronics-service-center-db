from service_center.visualization import generate_all_artifacts


if __name__ == "__main__":
    for artifact in generate_all_artifacts():
        print(artifact)
