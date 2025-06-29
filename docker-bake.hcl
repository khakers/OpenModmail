target "_common" {
  args = {
    PYTHON_VERSION = "3.12"
  }
  platforms = ["linux/amd64", "linux/arm64"]
}

target "openmodmail" {
  name = "openmodmail${notequal("",INCLUDE_SUPPORTUTILS) ? "-supportutils" : ""}${notequal("",INCLUDE_PIP) ? "-pip"  : ""}"
  inherits = ["_common"]
  context    = "."
  dockerfile = "Dockerfile"
  matrix = {
    INCLUDE_SUPPORTUTILS = ["true", ""]
    INCLUDE_PIP          = ["true", ""]
  }
}

# target "openmodmail-supportutils" {
#   inherits = ["_common"]
#   context    = "."
#   dockerfile = "Dockerfile"
#   args = {
#     INCLUDE_SUPPORTUTILS = "true"
#   }
# }
#
# target "openmodmail-pip" {
#   inherits = ["_common"]
#   context    = "."
#   dockerfile = "Dockerfile"
#   args = {
#     INCLUDE_PIP = "true"
#   }
# }
