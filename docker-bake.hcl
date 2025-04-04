target "_common" {
  args = {
    PYTHON_VERSION = "3.11"
  }
  platforms = ["linux/amd64", "linux/arm64"]
}

target "openmodmail" {
  inherits = ["_common"]
  context    = "."
  dockerfile = "Dockerfile"
}

target "openmodmail-supportutils" {
  inherits = ["_common"]
  context    = "."
  dockerfile = "Dockerfile"
  args = {
    INCLUDE_SUPPORTUTILS = "true"
  }
}
