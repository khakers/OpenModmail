target "_common" {
  args = {
    PYTHON_VERSION = "3.12"
  }
  platforms = ["linux/amd64", "linux/arm64"]
}

# placeholder for docker-metadata-action target data
target "docker-metadata-action" {
  tags = []
}

target "openmodmail" {
  name = "openmodmail${notequal("true",include-supportutils) ? "" : "-supportutils"}${notequal("true",include-pip) ? "" : "-pip"}"
  inherits = ["_common", "docker-metadata-action"]
  context    = "."
  dockerfile = "Dockerfile"
  matrix = {
    include-supportutils = ["true", "false"]
    include-pip          = ["true", "false"]
  }
  args = {
    INCLUDE_SUPPORTUTILS = include-supportutils
    INCLUDE_PIP          = include-pip
  }
  # take the tags from the docker-metadata-action target and append the suffixes based on the matrix values
  tags = [for tag in target.docker-metadata-action.tags : "${tag}${notequal("true",include-supportutils) ? "" : "-supportutils"}${notequal("true",include-pip) ? "" : "-pip"}"]
}
