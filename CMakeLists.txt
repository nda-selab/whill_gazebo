cmake_minimum_required(VERSION 3.8)
project(whill_gazebo)

find_package(
  ament_cmake REQUIRED
)

# ============================================================
# Install Gazebo models
# ============================================================

install(
  DIRECTORY models
  DESTINATION share/${PROJECT_NAME}
)

# ============================================================
# Install Gazebo worlds
# ============================================================

install(
  DIRECTORY worlds
  DESTINATION share/${PROJECT_NAME}
)


# ============================================================
# Install launch files
# ============================================================

install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
